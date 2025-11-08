"""
Módulo de transcripción usando OpenAI Whisper
Convierte audio a texto con detección automática de idioma
"""
import whisper
import numpy as np
import logging
import torch
from typing import Optional, Dict, Any
from dataclasses import dataclass

from config import config


logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    """Resultado de transcripción"""
    text: str
    language: str
    confidence: float = 0.0
    segments: Optional[list] = None
    

class WhisperTranscriber:
    """Transcriptor usando OpenAI Whisper"""
    
    def __init__(self):
        self.model: Optional[whisper.Whisper] = None
        self.is_loaded = False
        
    def load_model(self) -> bool:
        """Carga el modelo Whisper"""
        if self.is_loaded:
            return True
            
        try:
            logger.info(f"Cargando modelo Whisper '{config.transcription.model_size}'...")
            
            # Determinar dispositivo
            device = config.transcription.device
            if device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # Cargar modelo
            self.model = whisper.load_model(
                config.transcription.model_size,
                device=device
            )
            
            self.is_loaded = True
            logger.info(f"Modelo Whisper cargado en {device}")
            return True
            
        except Exception as e:
            logger.error(f"Error al cargar modelo Whisper: {e}")
            return False
    
    def transcribe(
        self, 
        audio_data: np.ndarray,
        language: Optional[str] = None
    ) -> Optional[TranscriptionResult]:
        """
        Transcribe audio a texto
        
        Args:
            audio_data: Array de audio normalizado [-1, 1]
            language: Código de idioma (opcional)
            
        Returns:
            Resultado de transcripción o None si falla
        """
        if not self.is_loaded:
            if not self.load_model():
                return None
        
        try:
            # Usar idioma configurado si no se especifica
            if language is None:
                language = config.transcription.language
            
            # Preparar opciones de transcripción
            options = {
                "language": language if language != "auto" else None,
                "task": "transcribe",
                "fp16": torch.cuda.is_available(),  # Usar FP16 si hay GPU
                "verbose": config.debug_mode
            }
            
            # Realizar transcripción
            logger.debug("Iniciando transcripción...")
            
            if self.model is None:
                logger.error("Modelo Whisper no está cargado")
                return None
                
            result = self.model.transcribe(audio_data, **options)
            
            # Procesar resultado
            text = str(result.get("text", "")).strip()
            detected_language = str(result.get("language", language))
            
            # Calcular confianza promedio de segmentos
            confidence = 0.0
            segments = result.get("segments", [])
            
            if segments and isinstance(segments, list):
                # Whisper no proporciona confidence directamente
                # Usar longitud de texto como proxy de confianza
                confidence = min(1.0, len(text) / 100.0)
            
            transcription_result = TranscriptionResult(
                text=text,
                language=detected_language,
                confidence=confidence,
                segments=segments if isinstance(segments, list) else []
            )
            
            logger.debug(f"Transcripción completada: '{text[:50]}...'")
            return transcription_result
            
        except Exception as e:
            logger.error(f"Error en transcripción: {e}")
            return None
    
    def transcribe_with_timestamps(
        self, 
        audio_data: np.ndarray,
        language: Optional[str] = None
    ) -> Optional[TranscriptionResult]:
        """
        Transcribe con timestamps detallados
        
        Args:
            audio_data: Array de audio normalizado
            language: Código de idioma
            
        Returns:
            Resultado con segmentos y timestamps
        """
        if not self.is_loaded:
            if not self.load_model():
                return None
        
        try:
            # Usar idioma configurado si no se especifica
            if language is None:
                language = config.transcription.language
            
            # Opciones para transcripción con timestamps
            options = {
                "language": language if language != "auto" else None,
                "task": "transcribe",
                "fp16": torch.cuda.is_available(),
                "verbose": config.debug_mode,
                "word_timestamps": True  # Habilitar timestamps por palabra
            }
            
            # Realizar transcripción
            if self.model is None:
                logger.error("Modelo Whisper no está cargado")
                return None
                
            result = self.model.transcribe(audio_data, **options)
            
            # Procesar resultado
            text = str(result.get("text", "")).strip()
            detected_language = str(result.get("language", language))
            segments = result.get("segments", [])
            
            # Calcular confianza
            confidence = 0.0
            if segments and isinstance(segments, list):
                # Usar número de palabras como proxy
                word_count = sum(len(seg.get("words", [])) if isinstance(seg, dict) else 0 for seg in segments)
                confidence = min(1.0, word_count / 50.0)
            
            transcription_result = TranscriptionResult(
                text=text,
                language=detected_language,
                confidence=confidence,
                segments=segments if isinstance(segments, list) else []
            )
            
            return transcription_result
            
        except Exception as e:
            logger.error(f"Error en transcripción con timestamps: {e}")
            return None
    
    def is_speech_detected(self, audio_data: np.ndarray, threshold: float = 0.01) -> bool:
        """
        Detecta si hay habla en el audio usando análisis simple
        
        Args:
            audio_data: Array de audio
            threshold: Umbral de energía para considerar habla
            
        Returns:
            True si se detecta posible habla
        """
        if len(audio_data) == 0:
            return False
        
        # Calcular energía RMS
        rms_energy = np.sqrt(np.mean(audio_data ** 2))
        
        # Verificar si supera el umbral
        return rms_energy > threshold
    
    def get_model_info(self) -> Dict[str, Any]:
        """Obtiene información del modelo cargado"""
        if not self.is_loaded or self.model is None:
            return {"loaded": False}
        
        try:
            device = next(self.model.parameters()).device
        except (AttributeError, StopIteration):
            device = "unknown"
        
        return {
            "loaded": True,
            "model_size": config.transcription.model_size,
            "device": str(device),
            "language": config.transcription.language
        }


def test_transcriber():
    """Test básico del transcriptor"""
    logging.basicConfig(level=logging.INFO)
    
    # Crear audio de prueba (silencio)
    duration = 2.0
    sample_rate = config.audio.sample_rate
    audio_data = np.zeros(int(duration * sample_rate), dtype=np.float32)
    
    # Agregar un poco de ruido para simular habla
    noise = np.random.normal(0, 0.01, audio_data.shape).astype(np.float32)
    audio_data += noise
    
    transcriber = WhisperTranscriber()
    
    if transcriber.load_model():
        print("Modelo Whisper cargado correctamente")
        
        # Test de detección de habla
        has_speech = transcriber.is_speech_detected(audio_data)
        print(f"¿Habla detectada?: {has_speech}")
        
        # Test de transcripción
        result = transcriber.transcribe(audio_data)
        if result:
            print(f"Transcripción: '{result.text}'")
            print(f"Idioma: {result.language}")
            print(f"Confianza: {result.confidence:.2f}")
        else:
            print("No se pudo transcribir")
            
        # Info del modelo
        info = transcriber.get_model_info()
        print(f"Info del modelo: {info}")
    else:
        print("Error al cargar modelo Whisper")


if __name__ == "__main__":
    test_transcriber()