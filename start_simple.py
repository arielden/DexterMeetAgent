#!/usr/bin/env python3
"""
Iniciador automático para DexterMeetAgent con interfaz web push-to-talk
"""

import threading
import time
import sys
import os

def run_web_server():
    """Ejecuta el servidor web en un thread separado"""
    try:
        # Importar y ejecutar el servidor web
        import web_server
        web_server.web_server.start_server()
    except Exception as e:
        print(f"Error en servidor web: {e}")

def main():
    """Función principal"""
    print("🚀 INICIANDO DEXTERMEETAGENT CON INTERFAZ WEB")
    print("=" * 60)
    
    # Iniciar servidor web en thread separado
    print("🌐 Iniciando servidor web...")
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Esperar que el servidor web se inicie
    time.sleep(3)
    print("✅ Servidor web activo en http://localhost:5001")
    print("🎯 Iniciando DexterMeetAgent...")
    print()
    print("🌐 FRONTEND WEB: http://localhost:5001")
    print("📊 Las transcripciones aparecerán en el navegador")
    print("🔴 Usa el botón PUSH-TO-TALK para grabar")
    print("⏹️  Presiona Ctrl+C para detener")
    print("=" * 60)
    print()
    
    # Ejecutar DexterMeetAgent en el mismo proceso
    try:
        import main
        sys.exit(main.main())
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo DexterMeetAgent...")
    except Exception as e:
        print(f"Error en DexterMeetAgent: {e}")

if __name__ == "__main__":
    main()