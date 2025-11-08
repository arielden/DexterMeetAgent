"""
Configuración central del sistema de transcripción push-to-talk
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class AudioConfig:
    """Configuración de captura de audio"""
    sample_rate: int = 16000  # Hz - Whisper recomienda 16kHz
    chunk_size: int = 1024    # Tamaño del buffer
    channels: int = 1         # Mono
    
    # Buffer de finalización para evitar corte de audio
    end_buffer_seconds: float = 1.5  # Segundos adicionales después de soltar botón
    

@dataclass
class DiarizationConfig:
    """Configuración de diarización de speakers"""
    model_name: str = "pyannote/speaker-diarization-3.1"
@dataclass
class TranscriptionConfig:
    """Configuración de transcripción con Whisper"""
    model_size: str = "base"  # tiny, base, small, medium, large
    language: str = "es"      # español por defecto
    device: str = "cpu"       # o "cuda" si hay GPU
    

@dataclass
class LLMConfig:
    """Configuración del modelo de lenguaje Ollama"""
    base_url: str = "http://localhost:11434"
    model_name: str = "llama3.2:3b"  # o "mistral:7b"
    timeout: float = 30.0
    
    # Template del prompt
    prompt_template: str = (
        "Eres un asistente de clase. Responde la siguiente pregunta de forma "
        "concisa en máximo 2-3 oraciones:\n\n"
        "Pregunta: {transcription}\n\n"
        "Respuesta:"
    )


@dataclass
class SystemConfig:
    """Configuración general del sistema"""
    audio: AudioConfig
    transcription: TranscriptionConfig
    llm: LLMConfig
    
    # Configuraciones generales
    debug_mode: bool = False
    log_level: str = "INFO"
    
    def __init__(self):
        self.audio = AudioConfig()
        self.transcription = TranscriptionConfig()
        self.llm = LLMConfig()


# Instancia global de configuración
config = SystemConfig()


def load_config_from_env():
    """Carga configuración desde variables de entorno"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Modelo Ollama
    ollama_model = os.getenv("OLLAMA_MODEL")
    if ollama_model:
        config.llm.model_name = ollama_model
    
    # URL de Ollama
    ollama_url = os.getenv("OLLAMA_URL")
    if ollama_url:
        config.llm.base_url = ollama_url
    
    # Modo debug
    debug = os.getenv("DEBUG", "false").lower()
    config.debug_mode = debug in ("true", "1", "yes")
    
    return config