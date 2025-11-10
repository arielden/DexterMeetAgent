#!/usr/bin/env python3
"""
Script para indexar archivos de base de conocimientos en ChromaDB
Uso: python index_knowledge_base.py <ruta_al_archivo>
"""
import sys
import os
import logging
from pathlib import Path

# Agregar el directorio actual al path para importar módulos locales
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_client import index_knowledge_base_file, rag_client
from config import config

def setup_logging():
    """Configura el logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    """Función principal"""
    setup_logging()
    logger = logging.getLogger(__name__)

    if len(sys.argv) != 2:
        print("Uso: python index_knowledge_base.py <ruta_al_archivo>")
        print("Ejemplo: python index_knowledge_base.py knowledge_base.txt")
        sys.exit(1)

    file_path = sys.argv[1]

    # Verificar que el archivo existe
    if not os.path.exists(file_path):
        logger.error(f"Archivo no encontrado: {file_path}")
        sys.exit(1)

    # Verificar que es un archivo de texto
    if not file_path.lower().endswith(('.txt', '.md', '.rst')):
        logger.warning(f"El archivo '{file_path}' no parece ser un archivo de texto. Continuando de todos modos...")

    logger.info(f"Indexando archivo: {file_path}")
    logger.info(f"Configuración RAG: colección='{config.rag.collection_name}', modelo='{config.rag.embedding_model}'")

    # Indexar el archivo
    success = index_knowledge_base_file(file_path)

    if success:
        # Mostrar estadísticas
        stats = rag_client.get_collection_stats()
        logger.info("Indexación completada exitosamente!")
        logger.info(f"Estadísticas: {stats}")
        print(f"✅ Archivo '{file_path}' indexado correctamente en la base de conocimientos.")
    else:
        logger.error("Error durante la indexación")
        sys.exit(1)

if __name__ == "__main__":
    main()