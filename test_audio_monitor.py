#!/usr/bin/env python3
"""
Test de captura de monitor de audio con reproducción simultánea
"""
import subprocess
import time
import threading
import signal
import sys

def play_test_tone():
    """Reproduce un tono de prueba en Jabra"""
    try:
        # Reproducir un tono de 1kHz durante 5 segundos en Jabra
        jabra_sink = "alsa_output.usb-GN_Netcom_A_S_Jabra_EVOLVE_20_MS_A006CBE574B60A-00.analog-stereo"
        
        cmd = [
            'pactl', 'load-module', 'module-sine', 
            f'sink={jabra_sink}',
            'frequency=1000'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            module_id = result.stdout.strip()
            print(f"🔊 Reproduciendo tono de 1kHz en Jabra (module {module_id})")
            
            # Esperar 3 segundos
            time.sleep(3)
            
            # Detener el tono
            subprocess.run(['pactl', 'unload-module', module_id])
            print("🔇 Tono detenido")
        else:
            print(f"❌ Error reproduciendo tono: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error en play_test_tone: {e}")

def capture_monitor():
    """Captura del monitor mientras se reproduce el tono"""
    try:
        jabra_monitor = "alsa_output.usb-GN_Netcom_A_S_Jabra_EVOLVE_20_MS_A006CBE574B60A-00.analog-stereo.monitor"
        
        print(f"🎧 Capturando desde monitor: {jabra_monitor}")
        
        # Capturar 4 segundos de audio
        cmd = [
            'timeout', '4',
            'pacat', '--record',
            f'--device={jabra_monitor}',
            '--rate=16000',
            '--channels=1',
            '--format=s16le'
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode == 124:  # timeout exitcode
            audio_bytes = len(result.stdout)
            print(f"📊 Capturados {audio_bytes} bytes de audio")
            
            if audio_bytes > 1000:  # Más de 1KB indica que hay señal
                print("🎉 ¡ÉXITO! Monitor capturando audio correctamente")
                
                # Analizar la amplitud
                import numpy as np
                audio_data = np.frombuffer(result.stdout, dtype=np.int16)
                max_amplitude = np.max(np.abs(audio_data))
                print(f"📈 Amplitud máxima: {max_amplitude} (rango: 0-32767)")
                
                if max_amplitude > 1000:
                    print("✅ Señal de audio fuerte detectada")
                elif max_amplitude > 100:
                    print("⚠️ Señal de audio débil")
                else:
                    print("❌ Señal muy débil o silencio")
            else:
                print("❌ No se capturó audio suficiente")
        else:
            print(f"❌ Error en captura: código {result.returncode}")
            
    except Exception as e:
        print(f"❌ Error en capture_monitor: {e}")

if __name__ == "__main__":
    print("🧪 Test de Monitor de Audio Jabra EVOLVE 20 MS")
    print("=" * 50)
    
    # Iniciar reproducción en hilo separado
    play_thread = threading.Thread(target=play_test_tone)
    play_thread.start()
    
    # Esperar un momento antes de empezar captura
    time.sleep(0.5)
    
    # Capturar audio
    capture_monitor()
    
    # Esperar que termine la reproducción
    play_thread.join()
    
    print("\n✅ Test completado")