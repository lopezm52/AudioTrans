#!/bin/bash

# Script de preparación para despliegue en Coolify
# Ejecutar: bash setup-production.sh

echo "🚀 Preparando AudioTrans para despliegue en Coolify..."

# Verificar que estamos en el directorio correcto
if [ ! -f "app.py" ]; then
    echo "❌ Error: No encontré app.py. ¿Estás en el directorio correcto?"
    exit 1
fi

# Generar API Key segura si no se especifica
if [ -z "$1" ]; then
    API_KEY=$(openssl rand -hex 16)
    echo "🔑 Generando API Key aleatoria: $API_KEY"
else
    API_KEY=$1
    echo "🔑 Usando API Key proporcionada: $API_KEY"
fi

echo ""
echo "📋 Resumen de archivos creados para producción:"
echo "  ✅ docker-compose.prod.yml - Configuración optimizada para Coolify"
echo "  ✅ Dockerfile.prod - Imagen multi-stage optimizada"
echo "  ✅ .dockerignore - Exclusión de archivos innecesarios"
echo "  ✅ DEPLOY.md - Guía completa de despliegue"

echo ""
echo "🔧 Variables de entorno requeridas en Coolify:"
echo "========================================"
echo "API_KEY=$API_KEY"
echo "OPENAI_API_KEY=sk-proj-tu-openai-key-real-aqui"
echo "WHISPER_MODEL=medium"
echo "MAX_FILE_SIZE=200MB"
echo "PORT=8000"
echo "========================================"

echo ""
echo "📝 Próximos pasos:"
echo "1. Sube este código a tu repositorio Git:"
echo "   git add ."
echo "   git commit -m 'Prepare for Coolify deployment'"
echo "   git push origin main"
echo ""
echo "2. En Coolify:"
echo "   - Crea nuevo servicio → Docker Compose"
echo "   - Conecta tu repositorio Git"
echo "   - Usa docker-compose.prod.yml"
echo "   - Configura las variables de entorno mostradas arriba"
echo ""
echo "3. Lee DEPLOY.md para instrucciones detalladas"
echo ""
echo "🎯 URL de test después del despliegue:"
echo "   https://tu-dominio.com/health"
echo ""
echo "💡 Tip: Cambia la API_KEY por una más segura en producción"
echo "✨ ¡Listo para desplegar en Coolify!" 