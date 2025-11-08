#!/bin/bash
# Activación automática del entorno virtual para DexterMeetAgent

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 DexterMeetAgent - Configurando entorno...${NC}"

# Verificar si estamos en el directorio correcto
if [ ! -f "main.py" ]; then
    echo -e "${YELLOW}⚠️  Navega al directorio del proyecto primero${NC}"
    echo "cd /media/arielden/DATA-M2/Projects/Software/DexterMeetAgent"
    return 1 2>/dev/null || exit 1
fi

# Activar entorno virtual
if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✅ Entorno virtual activado${NC}"
    echo -e "${GREEN}🐍 Python: $(python --version)${NC}"
    echo -e "${GREEN}📍 Ubicación: $(which python)${NC}"
else
    echo -e "${YELLOW}⚠️  Entorno virtual no encontrado. Creando...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    echo -e "${GREEN}✅ Entorno virtual creado y activado${NC}"
fi

# Verificar dependencias críticas
echo -e "${BLUE}🔍 Verificando dependencias...${NC}"
python -c "
import sys
required = ['flask', 'flask_socketio', 'whisper', 'torch', 'pyaudio', 'numpy']
missing = []
for pkg in required:
    try:
        __import__(pkg)
        print(f'✅ {pkg}')
    except ImportError:
        missing.append(pkg)
        print(f'❌ {pkg} - FALTA')

if missing:
    print(f'\\n⚠️  Instalar faltantes: pip install {\" \".join(missing)}')
else:
    print('\\n🎉 Todas las dependencias están instaladas')
"

echo -e "${BLUE}🎯 Entorno listo para DexterMeetAgent${NC}"
echo -e "${GREEN}▶️  Ejecutar: python start_simple.py${NC}"