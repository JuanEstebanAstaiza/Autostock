#!/bin/bash

# Autostock - Script de inicio rápido
# Este script configura y ejecuta la aplicación Autostock

echo "🚀 Iniciando Autostock..."

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado. Instálalo primero."
    exit 1
fi

# Verificar si estamos en el directorio correcto
if [ ! -f "requirements.txt" ]; then
    echo "❌ No se encuentra requirements.txt. Asegúrate de estar en el directorio raíz del proyecto."
    exit 1
fi

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Instalar dependencias
echo "📚 Instalando dependencias..."
pip install -r requirements.txt

# Verificar si existe la base de datos
if [ ! -f "app/database/inventario.db" ]; then
    echo "🗄️ Inicializando base de datos..."
    cd app
    python init_db.py
    cd ..
else
    echo "✅ Base de datos ya existe"
fi

# Asegurar permisos del directorio database
if [ -d "app/database" ]; then
    chmod 755 app/database
    if [ -f "app/database/inventario.db" ]; then
        chmod 644 app/database/inventario.db
    fi
    echo "✅ Permisos de base de datos configurados"
fi

# Ejecutar la aplicación
echo "🎯 Iniciando servidor..."
echo ""
echo "📱 La aplicación estará disponible en: http://localhost:4553"
echo "👤 Usuario SuperAdmin: superadmin / admin123"
echo ""
echo "Presiona Ctrl+C para detener el servidor"
echo ""

cd app
python main.py
