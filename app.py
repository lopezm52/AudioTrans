from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import JSONResponse
import whisper
import openai
from pydub import AudioSegment
import os
import tempfile
import asyncio
from typing import List
import logging
import warnings
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Silenciar warnings de Whisper sobre FP16/FP32
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")
warnings.filterwarnings("ignore", category=UserWarning, module="whisper")

app = FastAPI(title="AudioTrans API", description="API para transcripción de audio con OpenAI")

# Configuración de API Key
API_KEY = os.getenv("API_KEY", "audio-trans-secret-key-2024")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configuración del modelo Whisper
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")

# Configuración de tamaño máximo de archivo (en bytes)
def parse_file_size(size_str: str) -> int:
    """Convierte string como '100MB' a bytes"""
    if not size_str:
        return 100 * 1024 * 1024  # 100MB por defecto
    
    try:
        size_str = size_str.upper().strip()
        if size_str.endswith('MB'):
            return int(float(size_str[:-2])) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(float(size_str[:-2])) * 1024 * 1024 * 1024
        elif size_str.endswith('KB'):
            return int(float(size_str[:-2])) * 1024
        else:
            return int(size_str)  # Asumir bytes
    except (ValueError, TypeError) as e:
        logger.warning(f"Error parseando tamaño de archivo '{size_str}': {e}. Usando 100MB por defecto.")
        return 100 * 1024 * 1024  # 100MB por defecto

MAX_FILE_SIZE = parse_file_size(os.getenv("MAX_FILE_SIZE", "100MB"))

if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY no está configurada. Asegúrate de configurarla para usar OpenAI Chat.")

openai.api_key = OPENAI_API_KEY

logger.info(f"Configuración cargada:")
logger.info(f"  - Modelo Whisper: {WHISPER_MODEL}")
logger.info(f"  - Tamaño máximo de archivo: {MAX_FILE_SIZE / (1024*1024):.1f}MB")

# Seguridad
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="API Key inválida")
    return api_key

# Cargar modelo Whisper al iniciar la aplicación
whisper_model = None

@app.on_event("startup")
async def load_whisper_model():
    global whisper_model
    logger.info(f"Cargando modelo Whisper: {WHISPER_MODEL}")
    try:
        whisper_model = whisper.load_model(WHISPER_MODEL)
        logger.info(f"Modelo Whisper '{WHISPER_MODEL}' cargado exitosamente")
    except Exception as e:
        logger.error(f"Error cargando modelo Whisper '{WHISPER_MODEL}': {e}")
        logger.info("Intentando cargar modelo 'small' como respaldo...")
        whisper_model = whisper.load_model("small")
        logger.info("Modelo Whisper 'small' cargado como respaldo")

def split_audio(audio_path: str, segment_duration: int = 300) -> List[str]:
    """
    Divide un archivo de audio en segmentos de duración específica (en segundos)
    Por defecto 300 segundos = 5 minutos
    """
    try:
        audio = AudioSegment.from_file(audio_path)
        duration_ms = len(audio)
        segment_duration_ms = segment_duration * 1000
        
        segment_paths = []
        
        # Crear directorio temporal
        temp_dir = tempfile.mkdtemp()
        
        # Dividir y guardar segmentos directamente
        for i in range(0, duration_ms, segment_duration_ms):
            segment = audio[i:i + segment_duration_ms]
            segment_path = os.path.join(temp_dir, f"segment_{i//segment_duration_ms:03d}.wav")
            segment.export(segment_path, format="wav")
            segment_paths.append(segment_path)
            logger.info(f"Segmento {len(segment_paths)} creado: {segment_path}")
        
        return segment_paths
        
    except Exception as e:
        logger.error(f"Error dividiendo audio: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando archivo de audio: {str(e)}")

def transcribe_audio_segments(segment_paths: List[str]) -> str:
    """
    Transcribe cada segmento de audio usando Whisper y une las transcripciones
    """
    if not whisper_model:
        raise HTTPException(status_code=503, detail="Modelo Whisper no disponible")
    
    transcriptions = []
    
    for i, segment_path in enumerate(segment_paths):
        try:
            logger.info(f"Transcribiendo segmento {i+1}/{len(segment_paths)}")
            result = whisper_model.transcribe(segment_path)
            
            # Verificar que el resultado tenga el formato esperado
            if isinstance(result, dict) and "text" in result:
                text = result["text"].strip()
                transcriptions.append(text)
                logger.info(f"Segmento {i+1} transcrito: {len(text)} caracteres")
            else:
                logger.warning(f"Formato inesperado en resultado del segmento {i+1}")
                transcriptions.append("")  # Agregar texto vacío para mantener orden
                
        except Exception as e:
            logger.error(f"Error transcribiendo segmento {i+1}: {e}")
            transcriptions.append("")  # Agregar texto vacío para mantener orden
    
    # Unir todas las transcripciones en orden, filtrando textos vacíos
    valid_transcriptions = [t for t in transcriptions if t]
    full_transcription = " ".join(valid_transcriptions)
    
    if not full_transcription.strip():
        raise HTTPException(status_code=500, detail="No se pudo transcribir ningún segmento de audio")
    
    return full_transcription

def cleanup_temp_files(file_paths: List[str]):
    """
    Limpia archivos temporales
    """
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Archivo temporal eliminado: {file_path}")
        except Exception as e:
            logger.warning(f"Error eliminando archivo {file_path}: {e}")

async def process_with_openai_chat(text: str, custom_prompt: str = None) -> str:
    """
    Procesa el texto transcrito con OpenAI Chat
    """
    if not OPENAI_API_KEY:
        return "OpenAI API Key no configurada. Transcripción completada sin procesamiento adicional."
    
    # Prompt por defecto si no se especifica uno personalizado
    default_prompt = """
    Eres un asistente experto en análisis de texto. Tu tarea es procesar la siguiente transcripción de audio:
    
    1. Corrige errores gramaticales y de puntuación
    2. Estructura el texto de manera coherente
    3. Identifica los puntos principales y temas tratados
    4. Proporciona un resumen ejecutivo al final
    
    Transcripción a procesar:
    """
    
    prompt = custom_prompt if custom_prompt else default_prompt
    full_message = f"{prompt}\n\n{text}"
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": full_message}
            ],
            max_tokens=4000,
            temperature=0.3
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error procesando con OpenAI: {e}")
        return f"Error procesando con OpenAI: {str(e)}. Transcripción original: {text}"

@app.get("/")
async def root():
    return {"message": "AudioTrans API - Servicio de transcripción de audio"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "whisper_model_loaded": whisper_model is not None,
        "whisper_model": WHISPER_MODEL,
        "max_file_size_mb": round(MAX_FILE_SIZE / (1024*1024), 1),
        "api_key_configured": bool(API_KEY),
        "openai_key_configured": bool(OPENAI_API_KEY)
    }

@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    custom_prompt: str = None,
    api_key: str = Depends(get_api_key)
):
    """
    Transcribe un archivo de audio .m4a y lo procesa con OpenAI Chat
    """
    # Verificar formato de archivo
    if not file.filename.lower().endswith('.m4a'):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .m4a")
    
    if not whisper_model:
        raise HTTPException(status_code=503, detail="Modelo Whisper no está disponible")
    
    temp_files = []
    
    try:
        # Guardar archivo subido temporalmente y verificar tamaño
        with tempfile.NamedTemporaryFile(delete=False, suffix='.m4a') as tmp_file:
            content = await file.read()
            
            # Verificar tamaño del archivo
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413, 
                    detail=f"Archivo demasiado grande. Tamaño máximo permitido: {MAX_FILE_SIZE / (1024*1024):.1f}MB"
                )
            
            tmp_file.write(content)
            input_file_path = tmp_file.name
            temp_files.append(input_file_path)
        
        logger.info(f"Archivo recibido: {file.filename}, tamaño: {len(content)} bytes ({len(content) / (1024*1024):.1f}MB)")
        
        # Dividir audio en segmentos de 5 minutos
        logger.info("🔄 Paso 1/3: Dividiendo audio en segmentos de 5 minutos...")
        segment_paths = split_audio(input_file_path, segment_duration=300)
        temp_files.extend(segment_paths)
        logger.info(f"✅ Audio dividido en {len(segment_paths)} segmentos")
        
        # Transcribir cada segmento
        logger.info("🎤 Paso 2/3: Iniciando transcripción con Whisper...")
        logger.info(f"   ⏱️  Tiempo estimado: {len(segment_paths) * 30} segundos aprox.")
        full_transcription = transcribe_audio_segments(segment_paths)
        
        logger.info(f"✅ Transcripción completada: {len(full_transcription)} caracteres")
        logger.info("🤖 Paso 3/3: Enviando a OpenAI para procesamiento...")
        
        # Procesar con OpenAI Chat
        processed_response = await process_with_openai_chat(full_transcription, custom_prompt)
        
        return JSONResponse(content={
            "status": "success",
            "original_filename": file.filename,
            "segments_processed": len(segment_paths),
            "transcription_length": len(full_transcription),
            "raw_transcription": full_transcription,
            "processed_response": processed_response,
            "message": "Audio transcrito y procesado exitosamente"
        })
    
    except Exception as e:
        logger.error(f"Error procesando audio: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando audio: {str(e)}")
    
    finally:
        # Limpiar archivos temporales
        cleanup_temp_files(temp_files)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 