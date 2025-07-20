#!/usr/bin/env python3
"""
Script de verificación para AudioTrans
Verifica que todas las configuraciones estén correctas antes del despliegue
"""

import os
import sys
from dotenv import load_dotenv

def check_env_file():
    """Verifica que el archivo .env existe y tiene las variables necesarias"""
    print("🔍 Verificando archivo .env...")
    
    if not os.path.exists('.env'):
        print("❌ Archivo .env no encontrado")
        print("   Ejecuta: cp env.example .env")
        return False
    
    load_dotenv()
    
    required_vars = ['API_KEY', 'OPENAI_API_KEY']
    optional_vars = ['WHISPER_MODEL', 'MAX_FILE_SIZE']
    
    missing_required = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith('sk-your-') or value == 'tu-openai-api-key-aqui':
            missing_required.append(var)
        else:
            print(f"✅ {var}: configurado")
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"ℹ️  {var}: usando valor por defecto")
    
    if missing_required:
        print(f"❌ Variables requeridas sin configurar: {', '.join(missing_required)}")
        return False
    
    return True

def check_docker_files():
    """Verifica que los archivos de Docker existen"""
    print("\n🐳 Verificando archivos Docker...")
    
    docker_files = ['Dockerfile', 'docker-compose.yml', 'requirements.txt']
    
    for file in docker_files:
        if os.path.exists(file):
            print(f"✅ {file}: existe")
        else:
            print(f"❌ {file}: no encontrado")
            return False
    
    return True

def check_app_files():
    """Verifica que los archivos principales existen"""
    print("\n📁 Verificando archivos de la aplicación...")
    
    app_files = ['app.py', 'test_api.py', 'README.md']
    
    for file in app_files:
        if os.path.exists(file):
            print(f"✅ {file}: existe")
        else:
            print(f"❌ {file}: no encontrado")
            return False
    
    return True

def check_whisper_model():
    """Verifica que el modelo Whisper especificado es válido"""
    print("\n🎤 Verificando configuración de Whisper...")
    
    valid_models = ['tiny', 'base', 'small', 'medium', 'large']
    whisper_model = os.getenv('WHISPER_MODEL', 'small')
    
    if whisper_model in valid_models:
        print(f"✅ Modelo Whisper '{whisper_model}' es válido")
        
        # Información sobre el modelo
        model_info = {
            'tiny': '~39MB RAM, muy rápido, precisión básica',
            'base': '~74MB RAM, rápido, precisión buena',
            'small': '~244MB RAM, velocidad media, precisión muy buena',
            'medium': '~769MB RAM, lento, precisión excelente',
            'large': '~1550MB RAM, muy lento, precisión máxima'
        }
        print(f"   Características: {model_info[whisper_model]}")
        return True
    else:
        print(f"❌ Modelo Whisper '{whisper_model}' no es válido")
        print(f"   Modelos válidos: {', '.join(valid_models)}")
        return False

def check_file_size():
    """Verifica que el tamaño máximo de archivo es válido"""
    print("\n📏 Verificando configuración de tamaño de archivo...")
    
    max_size = os.getenv('MAX_FILE_SIZE', '100MB')
    
    try:
        # Intentar parsear el tamaño
        size_str = max_size.upper().strip()
        if size_str.endswith('MB'):
            size_mb = float(size_str[:-2])
        elif size_str.endswith('GB'):
            size_mb = float(size_str[:-2]) * 1024
        elif size_str.endswith('KB'):
            size_mb = float(size_str[:-2]) / 1024
        else:
            size_mb = int(size_str) / (1024 * 1024)
        
        print(f"✅ Tamaño máximo de archivo: {max_size} (~{size_mb:.1f}MB)")
        
        if size_mb > 1000:  # > 1GB
            print("⚠️  Archivo muy grande, podría consumir mucha memoria")
        elif size_mb < 10:  # < 10MB
            print("⚠️  Tamaño muy pequeño, podría rechazar archivos válidos")
        
        return True
        
    except (ValueError, TypeError):
        print(f"❌ Formato de tamaño inválido: '{max_size}'")
        print("   Formatos válidos: '100MB', '1GB', '500KB'")
        return False

def main():
    print("🚀 AudioTrans - Verificación de Configuración")
    print("=" * 50)
    
    checks = [
        check_env_file,
        check_docker_files,
        check_app_files,
        check_whisper_model,
        check_file_size
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ¡Todas las verificaciones pasaron!")
        print("\n📋 Siguiente paso:")
        print("   docker-compose up --build")
        print("\n🔧 Para probar la API:")
        print("   python test_api.py tu-archivo.m4a")
    else:
        print("💔 Algunas verificaciones fallaron")
        print("   Revisa los errores arriba y corrige la configuración")
        sys.exit(1)

if __name__ == "__main__":
    main() 