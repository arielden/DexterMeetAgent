#!/usr/bin/env python3
"""
DexterMeetAgent - Sistema de transcripción inteligente con push-to-talk
Captura audio controlado por usuario y genera respuestas automáticas
"""
import sys
import time
import logging
import signal
import threading
import numpy as np
import os
import warnings

# Silenciar mensajes de ALSA y JACK
os.environ['ALSA_PCM_CARD'] = '0'
os.environ['ALSA_PCM_DEVICE'] = '0'

# CONFIGURACIÓN DE LOGGING MÍNIMO (antes de importar otros módulos)
logging.basicConfig(level=logging.ERROR, format='%(message)s')

# Silenciar bibliotecas externas
logging.getLogger('httpcore').setLevel(logging.CRITICAL)
logging.getLogger('httpx').setLevel(logging.CRITICAL)  
logging.getLogger('fsspec').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)
logging.getLogger('requests').setLevel(logging.CRITICAL)
logging.getLogger('werkzeug').setLevel(logging.CRITICAL)
logging.getLogger('engineio').setLevel(logging.CRITICAL)
logging.getLogger('socketio').setLevel(logging.CRITICAL)

# Silenciar módulos propios
logging.getLogger('transcriber').setLevel(logging.CRITICAL)
logging.getLogger('llm_client').setLevel(logging.CRITICAL)
logging.getLogger('audio_capture').setLevel(logging.CRITICAL)
logging.getLogger('main').setLevel(logging.CRITICAL)
logging.getLogger('dexter').setLevel(logging.CRITICAL)

# Silenciar warnings de PyAudio y Whisper
warnings.filterwarnings("ignore", category=UserWarning)

from audio_capture import AudioCapture
from transcriber import WhisperTranscriber
from llm_client import OllamaClient
from config import config, load_config_from_env


logger = logging.getLogger(__name__)

class DexterMeetAgent:
    """Agente principal de transcripción inteligente push-to-talk"""
    
    def __init__(self):
        # Componentes principales
        self.audio_capture = AudioCapture()
        self.transcriber = WhisperTranscriber()
        self.llm_client = OllamaClient()
        
        # Estado interno
        self.is_running = False
        self.target_participant = "Usuario"
        
        # Sistema de grabación controlada
        self.is_recording = False
        self.recording_buffer = []
        self.recording_start_time = None
        
        # Configuración mínima necesaria
        self.stop_event = threading.Event()
        
        # Conexión web
        self.web_connected = False
        self.init_web_connection()
        
        # Configurar manejador de señales
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def init_web_connection(self):
        """Inicializa conexión HTTP con el servidor web"""
        self.web_connected = True
        logger.info("🌐 Conectado al servidor web via HTTP")
    
    def send_to_web(self, event_type, data):
        """Envía datos al frontend web via HTTP POST"""
        try:
            import requests
            
            if event_type == 'transcription':
                url = "http://localhost:5001/api/transcription"
                requests.post(url, json=data, timeout=2)
                
            elif event_type == 'response':
                url = "http://localhost:5001/api/response" 
                requests.post(url, json=data, timeout=2)
                
        except Exception as e:
            logger.warning(f"Error enviando al frontend: {e}")
    
    # === SISTEMA DE GRABACIÓN CONTROLADA ===
    
    def recording_control_handler(self, action):
        """Maneja las señales de inicio/fin de grabación del frontend"""
        try:
            if action == 'start':
                return self.start_controlled_recording()
            elif action == 'stop':
                return self.stop_recording_speakers()
            else:
                return False
        except Exception as e:
            print(f"Error en control de grabación: {e}")
            return False
    
    def start_controlled_recording(self):
        """PASO 2: Inicia grabación del MONITOR (parlantes) al presionar el botón"""
        if self.is_recording:
            return True
        
        try:
            self.is_recording = True
            self.recording_buffer = []
            self.recording_start_time = time.time()
            
            # Usar captura de monitor en lugar de micrófono
            self.audio_capture.audio_callback = self.add_audio_to_recording
            success = self.audio_capture.start_monitor_capture_parec()
            
            if success:
                # Enviar estado al frontend
                self.send_to_web('status', {
                    'message': 'Capturando audio de parlantes...',
                    'status': 'recording'
                })
                return True
            else:
                self.is_recording = False
                return False
            
        except Exception as e:
            print(f"Error al iniciar captura: {e}")
            self.is_recording = False
            return False
    
    def stop_recording_speakers(self) -> bool:
        """PASO 3: Detiene captura de audio de parlantes y procesa"""
        if not self.is_recording:
            return True
        
        try:
            # BUFFER DE FINALIZACIÓN: Capturar tiempo adicional para evitar corte
            buffer_time = config.audio.end_buffer_seconds
            time.sleep(buffer_time)  # Esperar tiempo configurado antes de detener
            
            # Detener captura de monitor
            self.audio_capture.stop_monitor_capture()
            
            self.is_recording = False
            
            # Enviar estado al frontend
            self.send_to_web('status', {
                'message': 'Procesando y transcribiendo audio...',
                'status': 'processing'
            })
            
            # PASO 4: Procesar audio en hilo separado
            processing_thread = threading.Thread(target=self._process_recorded_audio)
            processing_thread.daemon = True
            processing_thread.start()
            
            return True
        except Exception as e:
            print(f"Error al detener grabación: {e}")
            return False
    
    def _process_recorded_audio(self):
        """PASO 4-5: Procesa y transcribe audio grabado directamente"""
        try:
            if not self.recording_buffer:
                self.send_to_web('status', {
                    'message': 'No hay audio para procesar',
                    'status': 'ready'
                })
                return
            
            # Combinar todo el audio grabado
            combined_audio = np.concatenate(self.recording_buffer)
            duration = len(combined_audio) / config.audio.sample_rate
            max_amplitude = np.max(np.abs(combined_audio))
            
            # Validación básica del audio
            if duration < 0.3:
                self.send_to_web('status', {
                    'message': 'Audio demasiado corto',
                    'status': 'ready'
                })
                return
                
            if max_amplitude < 0.0001:
                self.send_to_web('status', {
                    'message': 'No se detectó señal de audio',
                    'status': 'ready'
                })
                return
            
            # Transcribir directamente todo el audio
            transcription_result = self.transcriber.transcribe(combined_audio)
            
            # Manejar respuesta del transcriptor
            transcription = ""
            if transcription_result is None:
                self.send_to_web('status', {
                    'message': 'Error en la transcripción - resultado vacío',
                    'status': 'ready'
                })
                return
            elif hasattr(transcription_result, 'text'):
                transcription = transcription_result.text.strip()
            elif isinstance(transcription_result, str):
                transcription = transcription_result.strip()
            elif isinstance(transcription_result, dict) and 'text' in transcription_result:
                transcription = transcription_result['text'].strip()
            else:
                self.send_to_web('status', {
                    'message': 'Error en el formato de transcripción',
                    'status': 'ready'
                })
                return
            
            if len(transcription) < 3:
                self.send_to_web('status', {
                    'message': 'Transcripción muy corta o vacía',
                    'status': 'ready'
                })
                return
            
            # Enviar transcripción al frontend
            timestamp = time.strftime('%H:%M:%S')
            
            self.send_to_web('transcription', {
                'participant': 'Participante Meet',
                'message': transcription,
                'timestamp': timestamp
            })
            
            # Generar respuesta del LLM
            self._generate_llm_response(transcription)
            
            # Limpiar buffer
            self.recording_buffer = []
            
            # Estado listo para siguiente grabación
            self.send_to_web('status', {
                'message': 'Transcripción completada',
                'status': 'ready'
            })
            
        except Exception as e:
            print(f"Error procesando audio: {e}")
            self.send_to_web('status', {
                'message': f'Error procesando: {str(e)}',
                'status': 'error'
            })
    
    def add_audio_to_recording(self, audio_chunk):
        """Agrega chunk de audio al buffer de grabación si está activa"""
        if self.is_recording and self.recording_buffer is not None:
            self.recording_buffer.append(audio_chunk)
        # Si no estamos grabando, no hacer nada
    
    # === FIN SISTEMA DE GRABACIÓN CONTROLADA ===
    
    def _signal_handler(self, signum, frame):
        """Manejador de señales para shutdown limpio"""
        print("\nCerrando sistema...")
        self.stop()
        sys.exit(0)
    
    def initialize(self) -> bool:
        """Inicializa todos los componentes del sistema"""
        print("Iniciando DexterMeetAgent...")
        
        # Cargar configuración desde .env
        load_config_from_env()
        
        # Verificar Ollama (silencioso)
        if not self.llm_client.is_available:
            print("❌ Error: Ollama no disponible")
            print("Instalar: curl -fsSL https://ollama.ai/install.sh | sh")
            print("Ejecutar: ollama serve")
            return False
        
        if not self.llm_client.check_model_availability():
            print(f"Descargando modelo {config.llm.model_name}...")
            if not self.llm_client.pull_model():
                print("❌ Error al descargar modelo")
                return False
        
        # Inicializar transcriptor (silencioso)
        if not self.transcriber.load_model():
            print("❌ Error al cargar Whisper")
            return False
        
        # Configurar captura de audio (silencioso)
        monitor_device = self.audio_capture.find_monitor_device()
        if not monitor_device:
            print("❌ No se encontró dispositivo monitor de audio")
            return False
        
        print("✅ Sistema listo")
        return True
    
    def setup_participant_mapping(self) -> bool:
        """Configura el mapeo inicial de participante objetivo"""
        # Configuración automática sin preguntar
        self.target_participant = "Usuario"
        
        return True
    
    def run(self):
        """Ejecuta el loop principal del agente con sistema push-to-talk"""
        print("🌐 Sistema listo - http://localhost:5001")
        
        self.is_running = True
        
        try:
            # Loop de espera para push-to-talk
            while self.is_running:
                time.sleep(0.1)  # Sleep ligero para no consumir CPU
                    
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"Error en loop principal: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Detiene el agente y limpia recursos"""
        self.is_running = False
        
        # Limpiar recursos
        self.audio_capture.cleanup()

    def _generate_llm_response(self, transcription):
        """Genera respuesta usando LLM"""
        try:
            # Generar respuesta (con RAG si está habilitado)
            response = self.llm_client.generate_response(transcription, use_rag=config.use_rag)
            if response:
                timestamp = time.strftime('%H:%M:%S')
                
                # Extraer texto de la respuesta (response es un objeto LLMResponse)
                response_text = response.text if hasattr(response, 'text') else str(response)
                
                # Enviar respuesta al frontend
                self.send_to_web('response', {
                    'participant': 'DexterAI',
                    'message': response_text,
                    'timestamp': timestamp
                })
                
        except Exception as e:
            print(f"Error generando respuesta LLM: {e}")


def main() -> int:
    """Función principal"""
    print("🎯 DexterMeetAgent - Sistema Push-to-Talk para Transcripciones")
    print("="*60)
    
    agent = DexterMeetAgent()
    
    # Registrar callback de control de grabación con servidor web
    try:
        import sys
        sys.path.append('.')
        from web_server import web_server
        web_server.set_recording_callback(agent.recording_control_handler)
    except Exception as e:
        print(f"No se pudo registrar callback con servidor web: {e}")
    
    # Inicializar componentes
    if not agent.initialize():
        print("Error en inicialización, saliendo...")
        return 1
    
    # Configurar mapeo de participante (simplificado para push-to-talk)
    if not agent.setup_participant_mapping():
        print("Error en configuración de participante, saliendo...")
        return 1
    
    # Ejecutar monitoreo
    try:
        agent.run()
    except Exception as e:
        print(f"Error fatal: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())