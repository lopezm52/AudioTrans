# AudioTrans API

Una aplicación de transcripción de audio que utiliza OpenAI Whisper para transcribir archivos .m4a y OpenAI GPT para procesar las transcripciones.

## Características

- 🎵 **Soporte para archivos .m4a**: Acepta archivos de audio en formato M4A
- ⚡ **Procesamiento en segmentos**: Divide automáticamente archivos largos en segmentos de 5 minutos
- 🤖 **Transcripción con Whisper**: Utiliza el modelo "small" de OpenAI Whisper ejecutado localmente (configurable)
- 📝 **Procesamiento inteligente**: Procesa las transcripciones con OpenAI GPT para mejorar y analizar el contenido
- 🔐 **Autenticación con API Key**: Protección mediante API Key fija
- 🐳 **Docker Ready**: Completamente containerizada
- ⚡ **Manejo robusto de errores**: Recuperación automática y logging detallado
- 🔧 **Configuración flexible**: Variables de entorno desde archivo .env
- 📊 **Health check completo**: Monitoreo de estado y configuración

## Requisitos Previos

- Docker y Docker Compose instalados
- API Key de OpenAI (para el procesamiento con GPT)

## Instalación y Configuración

### 1. Clonar o crear el proyecto

```bash
mkdir audiotrans && cd audiotrans
# Copiar todos los archivos del proyecto aquí
```

### 2. Configurar variables de entorno

**Opción A: Usar archivo .env (Recomendado)**
```bash
# Copiar archivo de ejemplo
cp env.example .env

# Luego edita .env con tus valores reales
nano .env
```

**Opción B: Variables de entorno del sistema**
```bash
export API_KEY="tu-api-key-aqui"
export OPENAI_API_KEY="tu-openai-key-aqui"
export WHISPER_MODEL="small"
export MAX_FILE_SIZE="100MB"
```

**Contenido del archivo `.env`:**
```bash
# API Key fija para autenticación de la aplicación
API_KEY=audio-trans-secret-key-2024

# Tu API Key de OpenAI (obligatoria)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Configuraciones adicionales
WHISPER_MODEL=small        # tiny, base, small, medium, large
MAX_FILE_SIZE=100MB       # Tamaño máximo de archivo (KB, MB, GB)
```

**Importante**: La aplicación carga automáticamente las variables desde el archivo `.env`.

### 3. Verificar configuración (Opcional)

```bash
# Ejecutar script de verificación
python verify_setup.py
```

### 4. Construir y ejecutar con Docker Compose

```bash
# Construir y ejecutar la aplicación
docker-compose up --build

# O ejecutar en segundo plano
docker-compose up -d --build
```

La aplicación estará disponible en: http://localhost:8000

## Uso de la API

### Endpoints Disponibles

#### 1. Health Check
```bash
GET /health
```

Verifica el estado de la aplicación y muestra la configuración actual:

```json
{
  "status": "healthy",
  "whisper_model_loaded": true,
  "whisper_model": "small",
  "max_file_size_mb": 100.0,
  "api_key_configured": true,
  "openai_key_configured": true
}
```

#### 2. Transcripción de Audio
```bash
POST /transcribe
```

**Headers obligatorios:**
```
X-API-Key: audio-trans-secret-key-2024
Content-Type: multipart/form-data
```

**Parámetros:**
- `file`: Archivo de audio en formato .m4a (obligatorio)
- `custom_prompt`: Prompt personalizado para el procesamiento con OpenAI (opcional)

### Ejemplo de uso con cURL

```bash
curl -X POST "http://localhost:8000/transcribe" \
     -H "X-API-Key: audio-trans-secret-key-2024" \
     -F "file=@tu-archivo.m4a" \
     -F "custom_prompt=Analiza esta transcripción y extrae los puntos clave"
```

### Ejemplo de uso con Python

```python
import requests

url = "http://localhost:8000/transcribe"
headers = {"X-API-Key": "audio-trans-secret-key-2024"}

files = {"file": open("tu-archivo.m4a", "rb")}
data = {"custom_prompt": "Analiza esta transcripción y proporciona un resumen"}

response = requests.post(url, headers=headers, files=files, data=data)
print(response.json())
```

## Respuesta de la API

La API devuelve un JSON con la siguiente estructura:

```json
{
  "status": "success",
  "original_filename": "audio.m4a",
  "segments_processed": 3,
  "transcription_length": 1250,
  "raw_transcription": "Transcripción completa del audio...",
  "processed_response": "Análisis procesado por OpenAI GPT...",
  "message": "Audio transcrito y procesado exitosamente"
}
```

## Proceso de Transcripción

1. **Recepción**: La API recibe el archivo .m4a
2. **Segmentación**: El audio se divide en fragmentos de 5 minutos
3. **Transcripción**: Cada segmento se transcribe usando Whisper (modelo medium)
4. **Unión**: Las transcripciones se unen manteniendo el orden correcto
5. **Procesamiento**: El texto completo se envía a OpenAI GPT para análisis
6. **Respuesta**: Se devuelve tanto la transcripción original como el análisis procesado

## Configuración Avanzada

### Variables de Entorno

| Variable | Descripción | Valor por Defecto | Ejemplo |
|----------|-------------|-------------------|---------|
| `API_KEY` | API Key para autenticación | `audio-trans-secret-key-2024` | `mi-clave-secreta` |
| `OPENAI_API_KEY` | API Key de OpenAI | *Requerida* | `sk-proj-abc123...` |
| `WHISPER_MODEL` | Modelo de Whisper a usar | `small` | `medium`, `large` |
| `MAX_FILE_SIZE` | Tamaño máximo de archivo | `100MB` | `50MB`, `1GB`, `500KB` |

### Modelos de Whisper Disponibles

La aplicación carga el modelo configurado en `WHISPER_MODEL` desde el archivo `.env`:

| Modelo | Precisión | Velocidad | Uso de RAM | Recomendado para |
|--------|-----------|-----------|------------|-------------------|
| `tiny` | Básica | Muy rápida | ~39MB | Pruebas rápidas |
| `base` | Buena | Rápida | ~74MB | Desarrollo |
| `small` | Muy buena | Media | ~244MB | **Pruebas (por defecto)** |
| `medium` | Excelente | Lenta | ~769MB | **Producción** |
| `large` | Máxima | Muy lenta | ~1550MB | Casos críticos |

Para cambiar el modelo, simplemente edita el archivo `.env`:
```bash
# Cambiar a modelo más preciso
WHISPER_MODEL=medium

# O a modelo más rápido
WHISPER_MODEL=tiny
```

Luego reconstruye el contenedor: `docker-compose up --build`

### Manejo de Errores y Recuperación

La aplicación incluye manejo robusto de errores:

- **Transcripción parcial**: Si algunos segmentos fallan, continúa con los exitosos
- **Modelo de respaldo**: Si el modelo especificado falla, usa "small" automáticamente
- **Validación de archivos**: Verifica formato y tamaño antes de procesar
- **Limpieza automática**: Elimina archivos temporales incluso si hay errores
- **Logging detallado**: Información completa para debugging

### Personalización del Prompt

Puedes personalizar cómo OpenAI procesa las transcripciones enviando un `custom_prompt`:

```bash
curl -X POST "http://localhost:8000/transcribe" \
     -H "X-API-Key: audio-trans-secret-key-2024" \
     -F "file=@audio.m4a" \
     -F "custom_prompt=Extrae las tareas mencionadas y crea una lista numerada"
```

## Monitoreo y Logs

Para ver los logs en tiempo real:

```bash
docker-compose logs -f audiotrans
```

## Limitaciones

- Solo acepta archivos en formato .m4a
- Uso de RAM variable según el modelo Whisper seleccionado (ver tabla de modelos)
- Tamaño de archivo limitado por `MAX_FILE_SIZE` (100MB por defecto, configurable)
- Los archivos muy largos pueden tomar tiempo considerable en procesarse
- Límite de tokens de OpenAI GPT (4000 tokens por defecto)

## Solución de Problemas

### Error: "Modelo Whisper no está disponible"
- Verifica que el contenedor tenga suficiente memoria RAM
- Revisa los logs para ver si hay errores en la carga del modelo

### Error: "API Key inválida"
- Verifica que estés enviando el header `X-API-Key` correcto
- Confirma que el valor coincida con la variable de entorno `API_KEY`

### Error: "OpenAI API Key no configurada"
- Verifica que hayas configurado `OPENAI_API_KEY` en tu archivo `.env`
- Confirma que la API Key de OpenAI sea válida y tenga créditos

### Error: "Archivo demasiado grande"
- El archivo excede el límite configurado en `MAX_FILE_SIZE`
- Puedes aumentar el límite editando `.env`: `MAX_FILE_SIZE=200MB`
- O comprimir/dividir el archivo de audio antes de subirlo

### Error cargando modelo Whisper
- Verifica que el modelo especificado en `WHISPER_MODEL` sea válido
- Modelos válidos: `tiny`, `base`, `small`, `medium`, `large`
- La aplicación intentará cargar el modelo "small" como respaldo

## Desarrollo

Para desarrollar localmente:

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
python app.py
```

## Seguridad

- Cambia la `API_KEY` por defecto en producción
- Mantén tu `OPENAI_API_KEY` segura y no la commits al control de versiones
- Considera implementar rate limiting para APIs públicas

## Licencia

Este proyecto es de código abierto. Úsalo bajo tu propia responsabilidad. 