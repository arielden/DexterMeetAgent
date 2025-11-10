#!/usr/bin/env python3
"""
Script de prueba para verificar que RAG funciona correctamente
"""
import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_client import get_relevant_context, rag_client
from config import config

def test_rag():
    """Prueba básica del sistema RAG"""
    print("🧪 Probando sistema RAG...")
    print(f"📊 Estadísticas de la colección: {rag_client.get_collection_stats()}")

    # Preguntas de prueba sobre estadística descriptiva
    test_questions = [
        "¿Qué es la estadística descriptiva?",
        "¿Cuál es la diferencia entre población y muestra?",
        "¿Qué medidas de tendencia central existen?",
        "¿Cómo se calcula la media aritmética?",
        "¿Qué es la desviación típica?",
        "¿Qué es el coeficiente de variación?",
        "¿Cuáles son las escalas de medida?",
        "¿Qué es una distribución de frecuencias?"
    ]

    print("\n" + "="*50)
    print("🔍 PRUEBAS DE BÚSQUEDA RAG")
    print("="*50)

    for question in test_questions:
        print(f"\n❓ Pregunta: {question}")
        context = get_relevant_context(question)
        if context:
            print("📄 Contexto encontrado:")
            # Mostrar solo las primeras líneas para no saturar
            lines = context.split('\n')[:3]
            for line in lines:
                if line.strip():
                    print(f"   {line[:80]}{'...' if len(line) > 80 else ''}")
        else:
            print("❌ No se encontró contexto relevante")

    print("\n✅ Prueba completada!")

if __name__ == "__main__":
    test_rag()