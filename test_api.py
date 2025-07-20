#!/usr/bin/env python3
"""
Script de prueba para AudioTrans API
Permite probar la funcionalidad de transcripción de audio
"""

import requests
import sys
import os
from pathlib import Path

# Configuración de la API
API_URL = "http://localhost:8000"
API_KEY = "Adaynoa27Audiotranscript2024"

def test_health_check():
    """Verifica el estado de salud de la API"""
    print("🔍 Verificando estado de la API...")
    
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API funcionando correctamente")
            print(f"   Status: {data['status']}")
            print(f"   Modelo Whisper cargado: {data['whisper_model_loaded']}")
            print(f"   Modelo Whisper: {data.get('whisper_model', 'N/A')}")
            print(f"   Tamaño máximo de archivo: {data.get('max_file_size_mb', 'N/A')}MB")
            print(f"   API Key configurada: {data.get('api_key_configured', False)}")
            print(f"   OpenAI Key configurada: {data.get('openai_key_configured', False)}")
            return True
        else:
            print(f"❌ Error en health check: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar a la API. ¿Está ejecutándose en http://localhost:8000?")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def transcribe_audio(audio_file_path, custom_prompt=None):
    """Transcribe un archivo de audio usando la API"""
    if not os.path.exists(audio_file_path):
        print(f"❌ El archivo {audio_file_path} no existe")
        return False
    
    if not audio_file_path.lower().endswith('.m4a'):
        print("❌ Solo se aceptan archivos .m4a")
        return False
    
    print(f"🎵 Transcribiendo archivo: {audio_file_path}")
    
    headers = {"X-API-Key": API_KEY}
    
    files = {"file": open(audio_file_path, "rb")}
    data = {}
    if custom_prompt:
        data["custom_prompt"] = custom_prompt
    
    try:
        print("⏳ Enviando archivo a la API...")
        print("   📋 Esto puede tardar varios minutos dependiendo del tamaño del archivo...")
        print("   🔄 Procesando: división → transcripción → análisis con OpenAI...")
        
        response = requests.post(
            f"{API_URL}/transcribe",
            headers=headers,
            files=files,
            data=data,
            timeout=1800  # 30 minutos de timeout para archivos largos
        )
        
        files["file"].close()
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Transcripción completada exitosamente!")
            print(f"📄 Archivo original: {result['original_filename']}")
            print(f"🔢 Segmentos procesados: {result['segments_processed']}")
            print(f"📏 Longitud de transcripción: {result['transcription_length']} caracteres")
            print(f"\n📝 Transcripción original:")
            print("-" * 50)
            print(result['raw_transcription'])
            print("-" * 50)
            print(f"\n🤖 Análisis procesado:")
            print("-" * 50)
            print(result['processed_response'])
            print("-" * 50)
            
            # Guardar resultados en archivos
            base_name = Path(audio_file_path).stem
            
            # Guardar transcripción original
            with open(f"{base_name}_transcription.txt", "w", encoding="utf-8") as f:
                f.write(result['raw_transcription'])
            print(f"\n💾 Transcripción guardada en: {base_name}_transcription.txt")
            
            # Guardar análisis procesado
            with open(f"{base_name}_analysis.txt", "w", encoding="utf-8") as f:
                f.write(result['processed_response'])
            print(f"💾 Análisis guardado en: {base_name}_analysis.txt")
            
            return True
            
        elif response.status_code == 403:
            print("❌ API Key inválida. Verifica la configuración.")
            return False
        elif response.status_code == 400:
            print(f"❌ Error en la solicitud: {response.json().get('detail', 'Error desconocido')}")
            return False
        else:
            print(f"❌ Error en la transcripción: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout: La transcripción tardó demasiado tiempo")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def main():
    print("🎤 AudioTrans API - Script de Prueba")
    print("=" * 40)
    
    # Verificar estado de la API
    if not test_health_check():
        print("\n❌ La API no está disponible. Asegúrate de que esté ejecutándose con:")
        print("   docker-compose up -d --build")
        sys.exit(1)
    
    print("\n" + "=" * 40)
    
    # Solicitar archivo de audio
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
    else:
        audio_file = input("📁 Ingresa la ruta del archivo .m4a: ").strip()
    
    # Prompt personalizado opcional
    custom_prompt = input("💭 Prompt personalizado (opcional, Enter para usar el por defecto): ").strip()
    if not custom_prompt:
        custom_prompt = None
    
    print("\n" + "=" * 40)
    
    # Realizar transcripción
    success = transcribe_audio(audio_file, custom_prompt)
    
    if success:
        print("\n🎉 ¡Transcripción completada exitosamente!")
    else:
        print("\n💔 Error en la transcripción")
        sys.exit(1)

if __name__ == "__main__":
    main() 