# DexterMeetAgent 🎯

Sistema de transcripción inteligente para Google Meet que identifica a un participante específico, transcribe cuando habla y genera respuestas cortas usando LLM local.

## ✨ Características

- **Captura de audio** desde monitor de PulseAudio/PipeWire
- **Diarización de speakers** con pyannote.audio para identificar participantes
- **Transcripción** en tiempo real con OpenAI Whisper
- **Respuestas inteligentes** generadas con Ollama (LLM local)
- **Mapeo manual** de speaker_id a nombre de participante
- **Buffer inteligente** con detección de fin de intervención
- **Sin almacenamiento** de historial (privacidad)

## 🔧 Requisitos del Sistema

### Software
- **OS**: Linux (Ubuntu/Debian/Fedora/Arch)
- **Python**: 3.10+
- **Audio**: PulseAudio o PipeWire
- **GPU**: Opcional (CUDA para mejor rendimiento)

### Hardware Recomendado
- **RAM**: 8GB+ (16GB recomendado para modelos grandes)
- **CPU**: Moderna con soporte AVX
- **GPU**: NVIDIA con CUDA (opcional pero mejora rendimiento)

## 📦 Instalación

### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd DexterMeetAgent
```

### 2. Crear entorno virtual
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Instalar dependencias del sistema
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install portaudio19-dev python3-pyaudio pulseaudio-utils

# Fedora
sudo dnf install portaudio-devel python3-pyaudio pulseaudio-utils

# Arch Linux
sudo pacman -S portaudio python-pyaudio pulseaudio
```

### 5. Instalar y configurar Ollama
```bash
# Instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Iniciar servicio
ollama serve &

# Descargar modelo recomendado
ollama pull llama3.2:3b
# o para mayor calidad (más lento):
# ollama pull mistral:7b
```

### 6. Configurar HuggingFace Token
1. Crear cuenta en [HuggingFace](https://huggingface.co/)
2. Generar token en [Settings > Access Tokens](https://huggingface.co/settings/tokens)
3. Aceptar términos del modelo [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)

### 7. Crear archivo de configuración
```bash
cp .env.example .env
# Editar .env con tu token de HuggingFace
```

Contenido de `.env`:
```env
HUGGINGFACE_TOKEN=hf_tu_token_aqui
OLLAMA_MODEL=llama3.2:3b
OLLAMA_URL=http://localhost:11434
DEBUG=false
```

## 🚀 Uso

### 1. Verificar configuración de audio
```bash
# Listar dispositivos de audio
python audio_capture.py

# Verificar monitor de PulseAudio
pactl list sources | grep -i monitor
```

### 2. Iniciar Google Meet
1. Abrir Google Meet en navegador
2. Unirse a reunión
3. Asegurar que hay conversación activa

### 3. Ejecutar DexterMeetAgent
```bash
python main.py
```

### 4. Configuración inicial
1. El sistema capturará audio por 10 segundos
2. Se identificarán automáticamente los speakers
3. Elegir qué speaker corresponde al participante objetivo
4. El sistema iniciará monitoreo continuo

### Ejemplo de ejecución:
```
🎯 DexterMeetAgent - Transcripción Inteligente para Google Meet
============================================================

=== INICIALIZANDO DEXTERMEETAGENT ===
✓ Ollama configurado correctamente
✓ Whisper cargado correctamente
✓ Diarizador inicializado
✓ Dispositivo monitor: alsa_output.pci-0000_00_1f.3.analog-stereo.monitor

=== CONFIGURACIÓN DE PARTICIPANTE ===
Nombre del participante a monitorear: Juan Pérez

Capturando audio inicial para identificar speakers...
Capturando por 10 segundos...

=== SPEAKERS DETECTADOS ===
1. Speaker SPEAKER_00
   Segmentos: 3
   Duración total: 12.4s
   Tiempos: 2.1-5.3s 8.7-12.1s 15.2-18.9s

2. Speaker SPEAKER_01
   Segmentos: 2
   Duración total: 8.1s
   Tiempos: 0.5-2.0s 13.5-19.1s

¿Qué speaker corresponde a 'Juan Pérez'? (1-2): 1
✓ SPEAKER_00 mapeado a 'Juan Pérez'

=== INICIANDO MONITOREO ===
Presiona Ctrl+C para detener

============================================================
👤 Juan Pérez: ¿Alguien puede explicar cómo funciona la integración continua?
🤖 Asistente: La integración continua es una práctica donde los desarrolladores integran código frecuentemente, ejecutando pruebas automáticas para detectar errores temprano. Mejora la calidad del software y reduce conflictos.
============================================================
```

## ⚙️ Configuración

### Archivo `config.py`
Personalizar parámetros en `config.py`:

```python
# Audio
config.audio.sample_rate = 16000
config.audio.buffer_seconds = 5.0

# Modelos
config.transcription.model_size = "base"  # tiny, base, small, medium, large
config.llm.model_name = "llama3.2:3b"

# Prompt personalizado
config.llm.prompt_template = "Tu prompt personalizado: {transcription}"
```

### Variables de entorno (`.env`)
```env
HUGGINGFACE_TOKEN=hf_your_token_here
OLLAMA_MODEL=llama3.2:3b
OLLAMA_URL=http://localhost:11434
DEBUG=false
```

## 🧪 Pruebas

### Probar componentes individualmente:
```bash
# Audio
python audio_capture.py

# Diarización
python diarizer.py

# Transcripción
python transcriber.py

# LLM
python llm_client.py
```

## 🔧 Solución de Problemas

### Audio no se captura
```bash
# Verificar dispositivos PulseAudio
pactl list sources short

# Verificar permisos
groups $USER | grep audio

# Reiniciar PulseAudio
pulseaudio -k && pulseaudio --start
```

### Error de token HuggingFace
1. Verificar token en `.env`
2. Aceptar términos en [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)

### Ollama no responde
```bash
# Verificar estado
curl http://localhost:11434/api/tags

# Reiniciar servicio
pkill ollama && ollama serve &

# Verificar modelo
ollama list
```

### Rendimiento lento
1. **GPU**: Instalar CUDA y PyTorch con soporte GPU
2. **Modelo Whisper**: Usar `tiny` o `base` en lugar de `large`
3. **Modelo Ollama**: Usar `llama3.2:3b` en lugar de modelos más grandes

## 📊 Rendimiento Esperado

### Latencia típica:
- **Captura + Diarización**: 2-4s
- **Transcripción (Whisper base)**: 3-6s
- **Generación LLM**: 3-7s
- **Total**: 8-17s

### Precisión:
- **Diarización**: 85-95% (depende de calidad audio y número de speakers)
- **Transcripción**: 90-98% (español, audio claro)
- **Relevancia respuestas**: Depende del modelo LLM

## 🛠️ Arquitectura

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Google Meet   │────│  PulseAudio      │────│  AudioCapture    │
│   (navegador)   │    │  Monitor         │    │  (pyaudio)       │
└─────────────────┘    └──────────────────┘    └──────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│     Ollama      │────│    Main Loop     │────│   SpeakerDiarizer│
│   (LLM local)   │    │  (main.py)       │    │ (pyannote.audio) │
└─────────────────┘    └──────────────────┘    └──────────────────┘
                                │                         │
                                ▼                         ▼
                       ┌──────────────────┐    ┌──────────────────┐
                       │ WhisperTranscriber│    │   VAD + Buffer   │
                       │ (openai-whisper) │    │  (webrtcvad)     │
                       └──────────────────┘    └──────────────────┘
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 🔒 Privacidad

- **No se almacena audio** ni transcripciones
- **Procesamiento local** (sin APIs cloud)
- **Token HuggingFace** solo para descarga de modelos
- **Ollama local** sin envío de datos externos

## 📚 Referencias

- [OpenAI Whisper](https://github.com/openai/whisper)
- [pyannote.audio](https://github.com/pyannote/pyannote-audio)
- [Ollama](https://ollama.ai/)
- [PulseAudio](https://www.freedesktop.org/wiki/Software/PulseAudio/)

## 🆘 Soporte

Para reportar bugs o solicitar features, abrir un issue en GitHub.

---

**DexterMeetAgent** - Transcripción inteligente para reuniones virtuales 🎯