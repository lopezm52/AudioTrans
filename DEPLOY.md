# 🚀 Guía de Despliegue AudioTrans en Coolify v4.0.0-beta.420.6

Esta guía te ayudará a desplegar AudioTrans en tu servidor usando Coolify.

## 📋 Requisitos Previos

- ✅ Servidor con Coolify v4.0.0-beta.420.6 instalado
- ✅ Mínimo 2GB RAM (recomendado 4GB)
- ✅ API Key de OpenAI válida
- ✅ Repositorio Git con el código (GitHub/GitLab/etc.)

## 🔧 Configuración en Coolify

### **Paso 1: Crear Nuevo Proyecto**

1. **Acceder a Coolify Dashboard**
   ```
   https://tu-coolify-server.com
   ```

2. **Crear Nuevo Servicio**
   - Click en `+ Add Service`
   - Seleccionar `Docker Compose`

### **Paso 2: Configuración del Repositorio**

1. **Conectar Repositorio Git**
   ```
   Repository URL: https://github.com/tu-usuario/AudioTrans
   Branch: main (o tu branch principal)
   ```

2. **Configurar Build Settings**
   ```
   Build Command: docker compose -f docker-compose.prod.yml build
   Docker Compose File: docker-compose.prod.yml
   ```

### **Paso 3: Variables de Entorno**

En la sección **Environment Variables**, agregar:

```bash
# API Key personalizada (CAMBIAR)
API_KEY=tu-api-key-muy-segura-2024

# OpenAI API Key (OBLIGATORIO)
OPENAI_API_KEY=sk-proj-tu-openai-key-real-aqui

# Modelo Whisper (medium para producción)
WHISPER_MODEL=medium

# Tamaño máximo de archivo
MAX_FILE_SIZE=200MB

# Puerto (Coolify lo asigna automáticamente)
PORT=8001
```

### **Paso 4: Configuración de Red**

1. **Configurar Puerto**
   ```
Internal Port: 8001
Public Port: [Auto-asignado por Coolify]
```

2. **Health Check**
   ```
Health Check Path: /health
Health Check Port: 8001
```

### **Paso 5: Configuración de Recursos**

```yaml
Memory Limit: 2GB
Memory Reservation: 1GB
CPU Limit: 1 Core
```

## 🗂️ Estructura de Archivos para Coolify

Asegúrate de que tu repositorio tenga esta estructura:

```
AudioTrans/
├── app.py                    # Aplicación principal
├── requirements.txt          # Dependencias Python
├── Dockerfile               # Dockerfile original
├── Dockerfile.prod         # Dockerfile optimizado para producción
├── docker-compose.yml      # Desarrollo local
├── docker-compose.prod.yml # Producción (Coolify)
├── README.md               # Documentación
├── DEPLOY.md              # Esta guía
└── .gitignore             # Archivos a ignorar
```

## 🔐 Configuración de Seguridad

### **Variables de Entorno Seguras**

1. **API_KEY**: Cambia por una clave única y compleja
   ```bash
   API_KEY=$(openssl rand -hex 32)
   # O usa: audio-trans-SERVIDOR-$(date +%Y%m%d)
   ```

2. **OPENAI_API_KEY**: Tu clave real de OpenAI
   ```bash
   OPENAI_API_KEY=sk-proj-tu-clave-real-de-openai
   ```

### **Configuración de Firewall**

Si usas un firewall, abre los puertos necesarios:
```bash
# Para el tráfico HTTP/HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Para Coolify (si es necesario)
sudo ufw allow 8001
```

## 🚀 Proceso de Despliegue

### **Opción A: Despliegue Automático**

1. **Push a tu repositorio**
   ```bash
   git add .
   git commit -m "Deploy to production"
   git push origin main
   ```

2. **Coolify detectará los cambios y desplegará automáticamente**

### **Opción B: Despliegue Manual**

1. **En Coolify Dashboard:**
   - Ve a tu servicio AudioTrans
   - Click en `Deploy Now`
   - Monitorea los logs de construcción

## 📊 Monitoreo y Logs

### **Verificar Estado**

1. **Health Check**
   ```bash
   curl https://tu-dominio.com/health
   ```

   **Respuesta esperada:**
   ```json
   {
     "status": "healthy",
     "whisper_model_loaded": true,
     "whisper_model": "medium",
     "max_file_size_mb": 200.0,
     "api_key_configured": true,
     "openai_key_configured": true
   }
   ```

2. **Logs en Tiempo Real**
   - En Coolify: Ve a tu servicio → Logs
   - Verifica que veas:
     ```
     ✅ Modelo Whisper 'medium' cargado exitosamente
     INFO: Uvicorn running on http://0.0.0.0:8001
     ```

## 🧪 Prueba de Producción

### **Test API desde tu local**

```bash
# Cambiar URL por tu dominio real
export API_URL="https://tu-dominio.com"
export API_KEY="tu-api-key-muy-segura-2024"

# Test health check
curl "${API_URL}/health"

# Test transcripción
curl -X POST "${API_URL}/transcribe" \
     -H "X-API-Key: ${API_KEY}" \
     -F "file=@test-audio.m4a" \
     -F "custom_prompt=Transcribe y resume este audio"
```

## ⚠️ Troubleshooting

### **Problema: Modelo Whisper no carga**
```bash
# Verificar memoria disponible
free -h

# Cambiar a modelo más pequeño temporalmente
WHISPER_MODEL=small
```

### **Problema: Timeout en archivos grandes**
```bash
# Aumentar timeout en Coolify
# Settings → Environment → Add:
MAX_FILE_SIZE=500MB
```

### **Problema: OpenAI API no funciona**
```bash
# Verificar la clave
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

## 🔧 Configuración Avanzada

### **SSL/HTTPS**
Coolify maneja automáticamente SSL con Let's Encrypt. Asegúrate de:
1. Configurar el dominio en Coolify
2. Verificar que el DNS apunte a tu servidor

### **Backup de Datos**
```bash
# Las transcripciones se procesan en memoria
# No hay datos persistentes que respaldar
# Solo asegúrate de tener backup del código
```

### **Escalabilidad**
Para mayor carga, considera:
- Aumentar límites de memoria (4GB+)
- Usar modelo Whisper "large" para mejor calidad
- Implementar cola de trabajos para archivos muy largos

## 📞 Soporte

Si encuentras problemas:
1. Revisa los logs en Coolify
2. Verifica las variables de entorno
3. Confirma que el health check pase
4. Prueba localmente primero

## 🎯 URLs Importantes

Después del despliegue tendrás:
- **Health Check**: `https://tu-dominio.com/health`
- **API Docs**: `https://tu-dominio.com/docs`
- **Transcripción**: `https://tu-dominio.com/transcribe`

¡Tu AudioTrans estará listo para producción! 🚀 