"""
Cliente para interactuar con Ollama LLM local
Genera respuestas cortas basadas en transcripciones con soporte RAG
"""
import ollama
import logging
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass

from config import config
from rag_client import get_relevant_context


logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Respuesta del modelo de lenguaje"""
    text: str
    model: str
    processing_time: float
    tokens_generated: int = 0
    

class OllamaClient:
    """Cliente para Ollama LLM local"""
    
    def __init__(self):
        self.client = ollama.Client(host=config.llm.base_url)
        self.is_available = False
        self._check_availability()
        
    def _check_availability(self) -> bool:
        """Verifica si Ollama está disponible"""
        try:
            # Verificar si el servicio está ejecutándose
            models = self.client.list()
            self.is_available = True
            logger.info("Ollama está disponible")
            return True
            
        except Exception as e:
            self.is_available = False
            logger.warning(f"Ollama no está disponible: {e}")
            return False
    
    def check_model_availability(self, model_name: Optional[str] = None) -> bool:
        """
        Verifica si un modelo específico está disponible
        
        Args:
            model_name: Nombre del modelo (usa config por defecto)
            
        Returns:
            True si el modelo está disponible
        """
        if not self.is_available:
            return False
            
        model_name = model_name or config.llm.model_name
        
        try:
            models = self.client.list()
            
            # Verificar diferentes estructuras de respuesta
            if 'models' in models:
                # Estructura esperada: {'models': [{'name': '...', ...}, ...]}
                available_models = []
                for model in models['models']:
                    if isinstance(model, dict):
                        # Buscar el nombre en diferentes campos posibles
                        name = model.get('name') or model.get('model') or model.get('id', '')
                        available_models.append(name)
                    else:
                        # Si es string directamente o objeto con __str__
                        model_str = str(model)
                        # Extraer el nombre del modelo del string si tiene formato "model='nombre'"
                        if "model='" in model_str:
                            start = model_str.find("model='") + 7
                            end = model_str.find("'", start)
                            if end > start:
                                available_models.append(model_str[start:end])
                        else:
                            available_models.append(model_str)
            else:
                # Estructura alternativa
                available_models = [str(model) for model in models]
            
            logger.debug(f"Modelos disponibles encontrados: {available_models}")
            
            if model_name in available_models:
                logger.info(f"Modelo '{model_name}' está disponible")
                return True
            else:
                logger.warning(f"Modelo '{model_name}' no encontrado")
                logger.info(f"Modelos disponibles: {available_models}")
                return False
                
        except Exception as e:
            logger.error(f"Error al verificar modelo: {e}")
            return False
    
    def pull_model(self, model_name: Optional[str] = None) -> bool:
        """
        Descarga un modelo si no está disponible
        
        Args:
            model_name: Nombre del modelo a descargar
            
        Returns:
            True si se descargó correctamente
        """
        if not self.is_available:
            return False
            
        model_name = model_name or config.llm.model_name
        
        try:
            logger.info(f"Descargando modelo '{model_name}'...")
            self.client.pull(model_name)
            logger.info(f"Modelo '{model_name}' descargado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error al descargar modelo: {e}")
            return False
    
    def generate_response(
        self, 
        transcription: str,
        model_name: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        use_rag: bool = False,
        use_stop_tokens: bool = True
    ) -> Optional[LLMResponse]:
        """
        Genera respuesta basada en transcripción
        
        Args:
            transcription: Texto transcrito
            model_name: Modelo a usar (opcional)
            custom_prompt: Prompt personalizado (opcional)
            use_rag: Si usar RAG para contexto adicional
            use_stop_tokens: Si usar tokens de parada
            
        Returns:
            Respuesta del LLM o None si falla
        """
        if not self.is_available:
            logger.error("Ollama no está disponible")
            return None
        
        model_name = model_name or config.llm.model_name
        
        # Verificar que el modelo esté disponible
        if not self.check_model_availability(model_name):
            logger.info(f"Intentando descargar modelo '{model_name}'...")
            if not self.pull_model(model_name):
                return None
        
        # Obtener contexto RAG si está habilitado
        context = ""
        if use_rag:
            context = get_relevant_context(transcription)
            if context:
                logger.debug(f"Contexto RAG obtenido: {len(context)} caracteres")
            else:
                logger.debug("No se encontró contexto relevante para RAG")
        
        # Preparar prompt
        if custom_prompt:
            if use_rag and "{context}" in custom_prompt:
                prompt = custom_prompt.format(transcription=transcription, context=context)
            else:
                prompt = custom_prompt.format(transcription=transcription)
        else:
            if use_rag and context:
                prompt = config.llm.prompt_template.format(transcription=transcription, context=context)
            else:
                # Fallback al prompt sin contexto si no hay contexto RAG
                prompt = config.llm.prompt_template.replace("{context}\n\n", "").format(transcription=transcription)
        
        try:
            start_time = time.time()
            
            # Configurar stop tokens basado en el parámetro
            stop_tokens = ["¿Tienes", "¿Hay", "¿Necesitas", "¿Te", "Si quieres"] if use_stop_tokens else []
            
            # Generar respuesta
            response = self.client.generate(
                model=model_name,
                prompt=prompt,
                options={
                    "temperature": config.llm.temperature,
                    "top_p": config.llm.top_p,
                    "num_predict": config.llm.max_tokens,  # Ollama usa num_predict en lugar de max_tokens
                    "stop": stop_tokens  # Usar stop tokens condicionalmente
                }
            )
            
            processing_time = time.time() - start_time
            
            # Extraer texto de respuesta
            response_text = response['response'].strip()
            
            # Contar tokens (aproximado)
            tokens_generated = len(response_text.split())
            
            llm_response = LLMResponse(
                text=response_text,
                model=model_name,
                processing_time=processing_time,
                tokens_generated=tokens_generated
            )
            
            logger.debug(f"Respuesta generada en {processing_time:.2f}s: '{response_text[:50]}...'")
            return llm_response
            
        except Exception as e:
            logger.error(f"Error al generar respuesta: {e}")
            return None
    
    def generate_short_response(self, transcription: str) -> Optional[str]:
        """
        Genera respuesta optimizada para el asistente académico
        
        Args:
            transcription: Texto transcrito
            
        Returns:
            Texto de respuesta o None
        """
        # Prompt optimizado para respuestas directas y concisas
        short_prompt = (
            "Responde de forma directa y concisa en 2-4 oraciones. No uses saludos.\n\n"
            "Pregunta: {transcription}\n\n"
            "Respuesta directa:"
        )
        
        response = self.generate_response(
            transcription=transcription,
            custom_prompt=short_prompt,
            use_rag=True  # Usar RAG para mejor contexto
        )
        
        # Si la respuesta es muy corta, reintentar sin stop tokens
        if response is None:
            logger.debug("Reintentando sin stop tokens para respuesta más completa...")
            response = self.generate_response(
                transcription=transcription,
                custom_prompt=short_prompt,
                use_rag=True,
                use_stop_tokens=False  # Sin stop tokens para permitir respuestas más largas
            )
        
        if response:
            # Limpiar respuestas innecesariamente largas o con frases introductorias
            text = response.text.strip()
            
            # Remover frases introductorias comunes
            introductory_phrases = [
                "¡Excelente pregunta!",
                "¡Hola!",
                "Me alegra poder ayudarte",
                "¡Excelente pregunta, estudiante!",
                "Es una gran pregunta",
                "Claro, te puedo ayudar"
            ]
            
            for phrase in introductory_phrases:
                if text.startswith(phrase):
                    # Remover la frase y limpiar espacios
                    text = text[len(phrase):].strip()
                    # Si queda con un salto de línea al inicio, removerlo también
                    text = text.lstrip('\n').strip()
            
            # Verificar longitud mínima - si es muy corta, regenerar sin stop tokens
            if len(text.split()) < 10:
                logger.debug("Respuesta muy corta, reintentando sin stop tokens...")
                return None
            
            # Limitar a máximo 4 oraciones para mantener concisión sin ser excesivo
            sentences = [s.strip() for s in text.split('.') if s.strip()]
            if len(sentences) > 4:
                text = '. '.join(sentences[:4]) + '.'
            elif len(sentences) > 0:
                text = '. '.join(sentences) + '.'
            
            # Asegurar que termine con puntuación
            if text and not text[-1] in '.!?':
                text += '.'
                
            return text
            
        return None
    
    def get_available_models(self) -> list:
        """Obtiene lista de modelos disponibles"""
        if not self.is_available:
            return []
            
        try:
            models = self.client.list()
            return [model['name'] for model in models['models']]
        except Exception as e:
            logger.error(f"Error al listar modelos: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene estado del cliente Ollama"""
        return {
            "available": self.is_available,
            "base_url": config.llm.base_url,
            "configured_model": config.llm.model_name,
            "model_available": self.check_model_availability() if self.is_available else False,
            "available_models": self.get_available_models()
        }


def test_ollama_client():
    """Test básico del cliente Ollama"""
    logging.basicConfig(level=logging.INFO)
    
    client = OllamaClient()
    
    # Verificar estado
    status = client.get_status()
    print("Estado de Ollama:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    print()
    
    if not client.is_available:
        print("❌ Ollama no está disponible. Asegúrate de que esté ejecutándose:")
        print("   curl -fsSL https://ollama.ai/install.sh | sh")
        print("   ollama serve")
        return
    
    # Test de respuesta
    test_transcription = "¿Cuál es la capital de Francia?"
    
    print(f"Test de transcripción: '{test_transcription}'")
    
    response = client.generate_short_response(test_transcription)
    if response:
        print(f"✓ Respuesta: {response}")
    else:
        print("❌ No se pudo generar respuesta")
    
    # Test con transcripción más larga
    long_transcription = (
        "Me podrías explicar cómo funciona el algoritmo de ordenamiento "
        "burbuja y cuál es su complejidad temporal"
    )
    
    print(f"\nTest con pregunta larga: '{long_transcription}'")
    
    response = client.generate_response(long_transcription)
    if response:
        print(f"✓ Respuesta ({response.processing_time:.2f}s): {response.text}")
        print(f"  Modelo: {response.model}")
        print(f"  Tokens: {response.tokens_generated}")
    else:
        print("❌ No se pudo generar respuesta")


if __name__ == "__main__":
    test_ollama_client()