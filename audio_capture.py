#!/usr/bin/env python3
"""
Módulo de captura de audio desde PulseAudio monitor
Captura audio del sistema para transcripción en tiempo real
"""
import pyaudio
import numpy as np
import threading
import queue
import time
import logging
import subprocess
from typing import List, Optional, Callable
from dataclasses import dataclass

from config import config


logger = logging.getLogger(__name__)


@dataclass
class AudioDevice:
    """Información de dispositivo de audio"""
    index: int
    name: str
    channels: int
    sample_rate: int
    is_input: bool


class AudioCapture:
    """Capturador de audio desde monitor de PulseAudio"""
    
    def __init__(self):
        self.pyaudio_instance = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.capture_thread: Optional[threading.Thread] = None
        self.audio_callback: Optional[Callable] = None  # Callback para chunks de audio
        self.parec_process = None   # Proceso parec para captura monitor
        self.parec_thread = None    # Hilo para captura monitor
        
        # Buffer para acumulación de audio
        self.audio_buffer = []
        self.buffer_lock = threading.Lock()
        
    def list_audio_devices(self) -> List[AudioDevice]:
        """Lista todos los dispositivos de audio disponibles"""
        devices = []
        
        for i in range(self.pyaudio_instance.get_device_count()):
            try:
                device_info = self.pyaudio_instance.get_device_info_by_index(i)
                device = AudioDevice(
                    index=i,
                    name=str(device_info['name']),
                    channels=int(device_info['maxInputChannels']),
                    sample_rate=int(device_info['defaultSampleRate']),
                    is_input=int(device_info['maxInputChannels']) > 0
                )
                devices.append(device)
            except Exception as e:
                logger.warning(f"Error al obtener info del dispositivo {i}: {e}")
                
        return devices
    
    def find_microphone_device(self) -> Optional[AudioDevice]:
        """Encuentra el mejor dispositivo de micrófono disponible"""
        devices = self.list_audio_devices()
        
        # Buscar micrófonos (dispositivos de entrada sin "monitor")
        microphones = [
            device for device in devices 
            if (device.is_input and 
                "monitor" not in device.name.lower() and
                device.channels > 0)
        ]
        
        if not microphones:
            logger.error("No se encontró ningún micrófono")
            logger.info("Dispositivos de entrada disponibles:")
            for device in devices:
                if device.is_input:
                    logger.info(f"  {device.index}: {device.name}")
            return None
        
        # Preferir micrófonos USB/webcam
        for device in microphones:
            if any(keyword in device.name.lower() for keyword in ["usb", "webcam", "genius"]):
                logger.info(f"Usando micrófono: {device.name}")
                return device
        
        # Usar micrófono interno como fallback
        for device in microphones:
            if "analog" in device.name.lower() and "input" in device.name.lower():
                logger.info(f"Usando micrófono interno: {device.name}")
                return device
        
        # Usar el primer micrófono disponible
        device = microphones[0]
        logger.info(f"Usando micrófono: {device.name}")
        return device

    def find_audio_device(self) -> Optional[AudioDevice]:
        """Encuentra dispositivo de audio (mantiene compatibilidad)"""
        return self.find_microphone_device()
    
    def find_monitor_device(self) -> Optional[AudioDevice]:
        """Encuentra dispositivo Line In/Monitor para capturar audio del sistema"""
        devices = self.list_audio_devices()
        
        # Log todos los dispositivos para debugging
        logger.info("=== DISPOSITIVOS DE ENTRADA DETECTADOS ===")
        for device in devices:
            if device.is_input:
                logger.info(f"  {device.index}: {device.name} (canales: {device.channels})")
        
        logger.info("🎧 Configuración: Capturando del Line In/Monitor del sistema")
        
        # ESTRATEGIA 1: Buscar específicamente monitor de audio analógico
        for device in devices:
            if (device.is_input and 
                "monitor" in device.name.lower() and 
                "analog" in device.name.lower()):
                logger.info(f"🎵 Usando Monitor Analógico: {device.name}")
                return device
        
        # ESTRATEGIA 2: Usar PipeWire que debe acceder al monitor
        for device in devices:
            if device.is_input and "pipewire" in device.name.lower():
                logger.info(f"🎵 Usando PipeWire: {device.name}")
                return device
        
        # ESTRATEGIA 3: Usar dispositivo "default" (ya configurado como monitor)
        for device in devices:
            if device.is_input and "default" in device.name.lower():
                logger.info(f"🔧 Usando Default (Monitor): {device.name}")
                return device
        
        # ESTRATEGIA 3: Buscar dispositivos de audio analógico (pueden ser Line In)
        for device in devices:
            if (device.is_input and 
                ("analog" in device.name.lower() or "alc892" in device.name.lower()) and
                device.channels >= 1):
                logger.info(f"🎵 Usando Line In analógico: {device.name}")
                return device
        
        logger.error("❌ No se encontró dispositivo Line In/Monitor")
        logger.info("💡 Tip: Ejecuta 'pactl set-default-source <monitor>' primero")
        return None
    
    def start_capture(self, device_index: Optional[int] = None) -> bool:
        """Inicia la captura de audio"""
        if self.is_recording:
            logger.warning("La captura ya está activa")
            return False
            
        # Encontrar dispositivo si no se especifica
        if device_index is None:
            monitor_device = self.find_monitor_device()
            if not monitor_device:
                return False
            device_index = monitor_device.index
            
        try:
            # Configurar stream de audio
            self.stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=config.audio.channels,
                rate=config.audio.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=config.audio.chunk_size,
                stream_callback=self._audio_callback
            )
            
            self.is_recording = True
            self.stream.start_stream()
            
            logger.info(f"Iniciada captura de audio desde dispositivo {device_index}")
            return True
            
        except Exception as e:
            logger.error(f"Error al iniciar captura de audio: {e}")
            return False
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback para procesar audio capturado"""
        if status:
            logger.warning(f"Status de audio: {status}")
            
        # Convertir bytes a numpy array
        audio_data = np.frombuffer(in_data, dtype=np.int16)
        
        # Normalizar a float32 [-1, 1]
        audio_normalized = audio_data.astype(np.float32) / 32768.0
        
        # Agregar al buffer
        with self.buffer_lock:
            self.audio_buffer.append(audio_normalized)
            
        # También agregar a queue para procesamiento en tiempo real
        try:
            self.audio_queue.put_nowait((audio_normalized, time.time()))
        except queue.Full:
            logger.warning("Queue de audio lleno, descartando frames")
            
        return (None, pyaudio.paContinue)
    
    def get_audio_chunk(self, timeout: float = 1.0) -> Optional[tuple]:
        """Obtiene un chunk de audio del queue"""
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_buffered_audio(self, clear_buffer: bool = True) -> np.ndarray:
        """Obtiene todo el audio acumulado en el buffer"""
        with self.buffer_lock:
            if not self.audio_buffer:
                return np.array([], dtype=np.float32)
                
            # Concatenar todos los chunks
            audio_data = np.concatenate(self.audio_buffer)
            
            if clear_buffer:
                self.audio_buffer.clear()
                
            return audio_data
    
    def stop_capture(self):
        """Detiene la captura de audio"""
        if not self.is_recording:
            return
            
        self.is_recording = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            
        logger.info("Captura de audio detenida")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
    
    def cleanup(self):
        """Limpia recursos"""
        self.stop_capture()
        
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()
    
    def start_monitor_capture_parec(self):
        """
        Inicia captura de monitor usando parec (PipeWire) como alternativa a PyAudio
        Esto captura exactamente lo que sale por los parlantes
        """
        if self.is_recording:
            logger.warning("Ya hay una captura activa")
            return False
            
        try:
            # Usar monitor de audio analógico configurado previamente
            monitor_source = "alsa_output.pci-0000_08_00.6.analog-stereo.monitor"
            
            logger.info(f"🎵 MONITOR: Iniciando captura con parec desde {monitor_source}")
            
            # Comando parec para capturar del monitor
            self.parec_process = subprocess.Popen([
                'parec', 
                '--device', monitor_source,
                '--rate', str(config.audio.sample_rate),
                '--channels', '1',
                '--format', 's16le',
                '--raw'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
            
            self.is_recording = True
            
            # Hilo de lectura de parec
            self.parec_thread = threading.Thread(target=self._parec_capture_loop)
            self.parec_thread.daemon = True
            self.parec_thread.start()
            
            logger.info("✅ MONITOR: Captura parec iniciada - capturando audio de parlantes")
            return True
            
        except Exception as e:
            logger.error(f"❌ MONITOR: Error iniciando parec: {e}")
            return False
    
    def _parec_capture_loop(self):
        """Loop de captura para parec en hilo separado"""
        try:
            buffer_size = 1024  # Chunks de 1024 bytes
            chunk_count = 0
            
            while self.is_recording and self.parec_process and self.parec_process.poll() is None:
                # Verificar que stdout esté disponible
                if not self.parec_process.stdout:
                    break
                    
                # Leer chunk de audio raw
                chunk_bytes = self.parec_process.stdout.read(buffer_size)
                
                if not chunk_bytes:
                    break
                
                # Convertir bytes a numpy array (s16le -> float32 normalizado)
                audio_chunk = np.frombuffer(chunk_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                
                if len(audio_chunk) == 0:
                    continue
                
                # Llamar al callback si existe
                if hasattr(self, 'audio_callback') and self.audio_callback:
                    self.audio_callback(audio_chunk)
                
                # Agregar al buffer
                with self.buffer_lock:
                    self.audio_buffer.append(audio_chunk)
                
                # También agregar a queue
                try:
                    self.audio_queue.put_nowait((audio_chunk, time.time()))
                except queue.Full:
                    pass
                
                chunk_count += 1
                
                # Log cada 100 chunks para debugging
                if chunk_count % 100 == 0:
                    max_amp = np.max(np.abs(audio_chunk)) if len(audio_chunk) > 0 else 0
                    logger.debug(f"🎵 MONITOR chunk {chunk_count}, amplitud: {max_amp:.6f}")
                    
        except Exception as e:
            logger.error(f"❌ MONITOR: Error en loop parec: {e}")
        finally:
            logger.info("🔴 MONITOR: Loop de captura parec finalizado")
    
    def stop_monitor_capture(self):
        """Detiene la captura de monitor parec con buffer de finalización"""
        logger.info("🛑 Iniciando detención gradual de captura...")
        
        # Marcar que ya no estamos grabando para que el loop termine naturalmente
        self.is_recording = False
        
        # Esperar un momento para que el loop procese los últimos chunks
        time.sleep(0.2)
        
        # Ahora detener el proceso parec
        if hasattr(self, 'parec_process') and self.parec_process:
            try:
                self.parec_process.terminate()
                self.parec_process.wait(timeout=2)
                logger.debug("📋 Proceso parec terminado correctamente")
            except subprocess.TimeoutExpired:
                logger.warning("⚠️ Timeout esperando parec, forzando kill...")
                self.parec_process.kill()
            except Exception as e:
                logger.debug(f"Excepción al terminar parec: {e}")
            self.parec_process = None
            
        # Esperar a que el hilo de captura termine
        if hasattr(self, 'parec_thread') and self.parec_thread and self.parec_thread.is_alive():
            self.parec_thread.join(timeout=1)
            if self.parec_thread.is_alive():
                logger.warning("⚠️ Hilo de captura no terminó en el tiempo esperado")
        
        logger.info("✅ MONITOR: Captura parec detenida completamente")


def list_audio_devices_cli():
    """Función CLI para listar dispositivos de audio"""
    print("Dispositivos de audio disponibles:")
    print("-" * 50)
    
    with AudioCapture() as capture:
        devices = capture.list_audio_devices()
        
        for device in devices:
            input_output = "INPUT" if device.is_input else "OUTPUT"
            print(f"{device.index:2d}: {device.name}")
            print(f"    Tipo: {input_output}")
            print(f"    Canales: {device.channels}")
            print(f"    Sample Rate: {device.sample_rate}")
            print()


if __name__ == "__main__":
    # Solo mostrar dispositivos
    list_audio_devices_cli()