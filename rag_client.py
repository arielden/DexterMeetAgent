"""
Cliente RAG (Retrieval-Augmented Generation) usando ChromaDB
Indexa documentos y recupera contexto relevante para mejorar respuestas del LLM
"""
import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import config

logger = logging.getLogger(__name__)


class RAGClient:
    """Cliente para sistema RAG con ChromaDB"""

    def __init__(self):
        self.embedding_model = SentenceTransformer(config.rag.embedding_model)
        self.client = chromadb.PersistentClient(path=config.rag.persist_directory)
        self.collection = self._get_or_create_collection()

        # Text splitter para dividir documentos
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.rag.chunk_size,
            chunk_overlap=config.rag.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def _get_or_create_collection(self):
        """Obtiene o crea la colección en ChromaDB"""
        try:
            collection = self.client.get_collection(name=config.rag.collection_name)
            logger.info(f"Colección '{config.rag.collection_name}' cargada exitosamente")
        except Exception as e:
            # La colección no existe, crearla
            logger.info(f"Colección '{config.rag.collection_name}' no existe, creándola...")
            collection = self.client.create_collection(name=config.rag.collection_name)
            logger.info(f"Colección '{config.rag.collection_name}' creada")
        return collection

    def index_document(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Indexa un documento en la base de conocimientos

        Args:
            file_path: Ruta al archivo a indexar
            metadata: Metadatos adicionales para el documento

        Returns:
            True si se indexó correctamente, False en caso contrario
        """
        try:
            # Verificar que el archivo existe
            if not os.path.exists(file_path):
                logger.error(f"Archivo no encontrado: {file_path}")
                return False

            # Cargar documento
            loader = TextLoader(file_path, encoding='utf-8')
            documents = loader.load()

            if not documents:
                logger.error(f"No se pudo cargar el documento: {file_path}")
                return False

            # Dividir en chunks
            chunks = self.text_splitter.split_documents(documents)

            if not chunks:
                logger.error("No se pudieron crear chunks del documento")
                return False

            # Preparar datos para ChromaDB
            ids = []
            texts = []
            embeddings = []
            metadatas = []

            for i, chunk in enumerate(chunks):
                chunk_id = f"{Path(file_path).stem}_chunk_{i}"
                chunk_text = chunk.page_content.strip()

                if not chunk_text:
                    continue

                # Generar embedding
                embedding = self.embedding_model.encode(chunk_text).tolist()

                # Metadata del chunk
                chunk_metadata = {
                    "source": file_path,
                    "chunk_id": i,
                    "total_chunks": len(chunks)
                }
                if metadata:
                    chunk_metadata.update(metadata)

                ids.append(chunk_id)
                texts.append(chunk_text)
                embeddings.append(embedding)
                metadatas.append(chunk_metadata)

            # Agregar a la colección
            if ids:
                self.collection.add(
                    ids=ids,
                    documents=texts,
                    embeddings=embeddings,
                    metadatas=metadatas
                )

                logger.info(f"Indexado documento '{file_path}' con {len(ids)} chunks")
                return True
            else:
                logger.warning("No se encontraron chunks válidos para indexar")
                return False

        except Exception as e:
            logger.error(f"Error indexando documento {file_path}: {e}")
            return False

    def search_context(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Busca contexto relevante para una consulta

        Args:
            query: La consulta del usuario
            top_k: Número de resultados a devolver (usa config.rag.top_k si None)

        Returns:
            Lista de documentos relevantes con sus metadatos y scores
        """
        try:
            if top_k is None:
                top_k = config.rag.top_k

            # Generar embedding de la query
            query_embedding = self.embedding_model.encode(query).tolist()

            # Buscar en la colección
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=['documents', 'metadatas', 'distances']
            )

            # Formatear resultados
            context_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {}
                    distance = results['distances'][0][i] if results['distances'] and results['distances'][0] else 0.0

                    context_results.append({
                        'content': doc,
                        'metadata': metadata,
                        'score': 1.0 - distance  # Convertir distancia a similitud (0-1)
                    })

            logger.info(f"Búsqueda completada: {len(context_results)} resultados para query '{query[:50]}...'")
            return context_results

        except Exception as e:
            logger.error(f"Error en búsqueda de contexto: {e}")
            return []

    def get_collection_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la colección"""
        try:
            count = self.collection.count()
            return {
                'total_documents': count,
                'collection_name': config.rag.collection_name,
                'persist_directory': config.rag.persist_directory
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}

    def clear_collection(self) -> bool:
        """Limpia toda la colección (útil para reiniciar)"""
        try:
            self.client.delete_collection(name=config.rag.collection_name)
            self.collection = self.client.create_collection(name=config.rag.collection_name)
            logger.info("Colección limpiada exitosamente")
            return True
        except Exception as e:
            logger.error(f"Error limpiando colección: {e}")
            return False


# Instancia global del cliente RAG
rag_client = RAGClient()


def index_knowledge_base_file(file_path: str) -> bool:
    """
    Función de conveniencia para indexar un archivo de base de conocimientos

    Args:
        file_path: Ruta al archivo a indexar

    Returns:
        True si se indexó correctamente
    """
    return rag_client.index_document(file_path)


def get_relevant_context(query: str, top_k: Optional[int] = None) -> str:
    """
    Función de conveniencia para obtener contexto relevante formateado

    Args:
        query: La consulta del usuario
        top_k: Número de resultados

    Returns:
        Contexto formateado como string
    """
    results = rag_client.search_context(query, top_k)

    if not results:
        return ""

    # Formatear contexto
    context_parts = []
    for result in results:
        content = result['content'].strip()
        source = result['metadata'].get('source', 'Desconocido')
        context_parts.append(f"[{source}]\n{content}")

    return "\n\n".join(context_parts)