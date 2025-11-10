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
class RAGConfig:
    """Configuración del sistema RAG con ChromaDB"""
    collection_name: str = "knowledge_base"
    embedding_model: str = "all-MiniLM-L6-v2"  # Modelo de embeddings
    chunk_size: int = 1000  # Tamaño de chunks en caracteres
    chunk_overlap: int = 200  # Superposición entre chunks
    persist_directory: str = "./chroma_db"  # Directorio para persistir la DB
    top_k: int = 3  # Número de documentos relevantes a recuperar
    

@dataclass
class LLMConfig:
    """Configuración del modelo de lenguaje Ollama"""
    base_url: str = "http://localhost:11434"
    model_name: str = "llama3.2:3b"  # o "mistral:7b"
    timeout: float = 45.0  # Timeout más generoso
    max_tokens: int = 200  # Tokens para respuestas concisas pero informativas
    temperature: float = 0.7
    top_p: float = 0.9
    
    # Template del prompt con contexto RAG
    prompt_template: str = (
        "Responde de forma directa y concisa usando el contexto proporcionado. "
        "No uses saludos, solo proporciona la información solicitada.\n\n"
        "Contexto relevante:\n{context}\n\n"
        "Pregunta: {transcription}\n\n"
        "Respuesta:"
    )


@dataclass
class SystemConfig:
    """Configuración general del sistema"""
    audio: AudioConfig
    transcription: TranscriptionConfig
    llm: LLMConfig
    rag: RAGConfig
    
    # Configuraciones generales
    debug_mode: bool = False
    log_level: str = "INFO"
    use_rag: bool = True  # Habilitar RAG por defecto
    
    def __init__(self):
        self.audio = AudioConfig()
        self.transcription = TranscriptionConfig()
        self.llm = LLMConfig()
        self.rag = RAGConfig()
        self.rag = RAGConfig()


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