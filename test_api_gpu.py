#!/usr/bin/env python3
"""
Test script para AudioTrans GPU version
Incluye tests de rendimiento, monitoreo de memoria GPU y comparación con CPU
"""

import requests
import time
import os
import json
import argparse
from typing import Dict, Any
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AudioTransGPUTester:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {"X-API-Key": api_key}
        
        # URLs
        self.health_url = f"{self.base_url}/health"
        self.transcribe_url = f"{self.base_url}/transcribe"
        
        # Métricas
        self.results = []
        
    def test_health_check(self) -> Dict[str, Any]:
        """Verificar health check y obtener información del sistema"""
        logger.info("🔍 Realizando health check...")
        
        try:
            response = requests.get(self.health_url, timeout=30)
            response.raise_for_status()
            
            health_data = response.json()
            logger.info("✅ Health check exitoso")
            
            # Mostrar información relevante
            self._display_system_info(health_data)
            
            return health_data
            
        except Exception as e:
            logger.error(f"❌ Health check falló: {e}")
            return {}
    
    def _display_system_info(self, health_data: Dict[str, Any]):
        """Mostrar información del sistema de manera organizada"""
        print("\n" + "="*60)
        print("📊 INFORMACIÓN DEL SISTEMA")
        print("="*60)
        
        # Información básica
        print(f"📱 Estado: {health_data.get('status', 'unknown')}")
        print(f"🤖 Modelo Whisper: {health_data.get('whisper_model', 'unknown')}")
        print(f"🎯 Dispositivo: {health_data.get('device', 'unknown')} ({health_data.get('device_name', 'unknown')})")
        print(f"📦 Tamaño máximo: {health_data.get('max_file_size_mb', 'unknown')}MB")
        
        # Información GPU
        gpu_stats = health_data.get('gpu_stats', {})
        if gpu_stats.get('gpu_available'):
            print(f"\n🔥 GPU INFORMACIÓN:")
            print(f"   💻 Nombre: {gpu_stats.get('gpu_name', 'unknown')}")
            print(f"   🔢 GPUs: {gpu_stats.get('gpu_count', 'unknown')}")
            print(f"   💾 Memoria asignada: {gpu_stats.get('memory_allocated_gb', 'unknown')}GB")
            print(f"   🏛️ Memoria reservada: {gpu_stats.get('memory_reserved_gb', 'unknown')}GB")
            
            if gpu_stats.get('memory_total_gb'):
                print(f"   📊 Memoria total: {gpu_stats.get('memory_total_gb', 'unknown')}GB")
                print(f"   📈 Uso GPU: {gpu_stats.get('gpu_utilization', 'unknown')}%")
                print(f"   📉 Uso memoria: {gpu_stats.get('memory_utilization', 'unknown')}%")
        else:
            print(f"⚠️ GPU no disponible")
        
        # Información del sistema
        system_stats = health_data.get('system_stats', {})
        if system_stats:
            print(f"\n🖥️ SISTEMA:")
            print(f"   🧠 CPU: {system_stats.get('cpu_percent', 'unknown')}%")
            print(f"   💾 Memoria: {system_stats.get('memory_percent', 'unknown')}%")
            print(f"   🆓 Memoria disponible: {system_stats.get('available_memory_gb', 'unknown')}GB")
        
        print("="*60)
    
    def test_transcription_performance(self, test_file: str, custom_prompt: str = None) -> Dict[str, Any]:
        """Test de transcripción con medición de rendimiento"""
        logger.info(f"🎤 Iniciando test de transcripción: {test_file}")
        
        # Verificar archivo
        if not os.path.exists(test_file):
            logger.error(f"❌ Archivo no encontrado: {test_file}")
            return {}
        
        file_size_mb = os.path.getsize(test_file) / (1024 * 1024)
        logger.info(f"📁 Tamaño del archivo: {file_size_mb:.2f}MB")
        
        # Obtener estado inicial de memoria GPU
        initial_health = self.test_health_check()
        initial_gpu_memory = self._get_gpu_memory(initial_health)
        
        # Preparar archivo
        files = {"file": (os.path.basename(test_file), open(test_file, "rb"), "audio/m4a")}
        data = {}
        if custom_prompt:
            data["custom_prompt"] = custom_prompt
        
        # Realizar transcripción
        start_time = time.time()
        
        try:
            logger.info("🔄 Enviando archivo para transcripción...")
            response = requests.post(
                self.transcribe_url,
                files=files,
                data=data,
                headers=self.headers,
                timeout=1800  # 30 minutos timeout
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"✅ Transcripción completada en {processing_time:.2f} segundos")
            
            # Obtener estado final de memoria GPU
            final_health = self.test_health_check()
            final_gpu_memory = self._get_gpu_memory(final_health)
            
            # Calcular métricas
            metrics = self._calculate_metrics(
                file_size_mb, processing_time, result, 
                initial_gpu_memory, final_gpu_memory
            )
            
            self._display_transcription_results(result, metrics)
            
            return {
                "success": True,
                "metrics": metrics,
                "result": result
            }
            
        except requests.exceptions.Timeout:
            logger.error("❌ Timeout en transcripción")
            return {"success": False, "error": "timeout"}
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error en transcripción: {e}")
            return {"success": False, "error": str(e)}
        finally:
            files["file"][1].close()
    
    def _get_gpu_memory(self, health_data: Dict[str, Any]) -> Dict[str, float]:
        """Extraer información de memoria GPU del health check"""
        gpu_stats = health_data.get('gpu_stats', {})
        return {
            'allocated_gb': gpu_stats.get('memory_allocated_gb', 0),
            'reserved_gb': gpu_stats.get('memory_reserved_gb', 0),
            'utilization': gpu_stats.get('memory_utilization', 0)
        }
    
    def _calculate_metrics(self, file_size_mb: float, processing_time: float, 
                          result: Dict[str, Any], initial_memory: Dict[str, float], 
                          final_memory: Dict[str, float]) -> Dict[str, Any]:
        """Calcular métricas de rendimiento"""
        
        # Métricas básicas
        transcription_length = len(result.get('raw_transcription', ''))
        segments_processed = result.get('segments_processed', 0)
        
        # Velocidad de procesamiento
        mb_per_second = file_size_mb / processing_time if processing_time > 0 else 0
        chars_per_second = transcription_length / processing_time if processing_time > 0 else 0
        
        # Memoria GPU
        memory_delta = final_memory['allocated_gb'] - initial_memory['allocated_gb']
        
        return {
            'file_size_mb': file_size_mb,
            'processing_time': processing_time,
            'transcription_length': transcription_length,
            'segments_processed': segments_processed,
            'mb_per_second': mb_per_second,
            'chars_per_second': chars_per_second,
            'memory_usage_delta_gb': memory_delta,
            'initial_gpu_memory_gb': initial_memory['allocated_gb'],
            'final_gpu_memory_gb': final_memory['allocated_gb']
        }
    
    def _display_transcription_results(self, result: Dict[str, Any], metrics: Dict[str, Any]):
        """Mostrar resultados de la transcripción"""
        print("\n" + "="*60)
        print("📈 RESULTADOS DE TRANSCRIPCIÓN")
        print("="*60)
        
        # Métricas de rendimiento
        print(f"⏱️ Tiempo total: {metrics['processing_time']:.2f}s")
        print(f"🚀 Velocidad: {metrics['mb_per_second']:.2f} MB/s")
        print(f"📝 Caracteres/s: {metrics['chars_per_second']:.1f}")
        print(f"🔧 Segmentos procesados: {metrics['segments_processed']}")
        
        # Memoria GPU
        print(f"\n💾 MEMORIA GPU:")
        print(f"   Inicial: {metrics['initial_gpu_memory_gb']:.2f}GB")
        print(f"   Final: {metrics['final_gpu_memory_gb']:.2f}GB")
        print(f"   Delta: {metrics['memory_usage_delta_gb']:+.2f}GB")
        
        # Transcripción
        print(f"\n📝 TRANSCRIPCIÓN:")
        print(f"   Longitud: {metrics['transcription_length']} caracteres")
        print(f"   Preview: {result.get('raw_transcription', '')[:150]}...")
        
        print("="*60)
    
    def benchmark_suite(self, test_files: list, iterations: int = 1):
        """Ejecutar suite completo de benchmarks"""
        logger.info(f"🧪 Iniciando benchmark suite con {len(test_files)} archivos")
        
        all_results = []
        
        for i in range(iterations):
            logger.info(f"🔄 Iteración {i+1}/{iterations}")
            
            for test_file in test_files:
                if os.path.exists(test_file):
                    result = self.test_transcription_performance(test_file)
                    if result.get('success'):
                        all_results.append({
                            'iteration': i + 1,
                            'file': test_file,
                            'metrics': result['metrics']
                        })
                    
                    # Pausa entre tests para limpiar memoria
                    time.sleep(5)
                else:
                    logger.warning(f"⚠️ Archivo no encontrado: {test_file}")
        
        if all_results:
            self._display_benchmark_summary(all_results)
        else:
            logger.warning("⚠️ No se obtuvieron resultados válidos")
    
    def _display_benchmark_summary(self, results: list):
        """Mostrar resumen de todos los benchmarks"""
        print("\n" + "="*80)
        print("📊 RESUMEN DE BENCHMARKS")
        print("="*80)
        
        # Calcular estadísticas
        processing_times = [r['metrics']['processing_time'] for r in results]
        speeds = [r['metrics']['mb_per_second'] for r in results]
        memory_deltas = [r['metrics']['memory_usage_delta_gb'] for r in results]
        
        print(f"📋 Total de tests: {len(results)}")
        print(f"⏱️ Tiempo promedio: {sum(processing_times)/len(processing_times):.2f}s")
        print(f"⚡ Velocidad promedio: {sum(speeds)/len(speeds):.2f} MB/s")
        print(f"💾 Uso memoria promedio: {sum(memory_deltas)/len(memory_deltas):+.2f}GB")
        
        print("\n📈 Detalles por archivo:")
        for result in results:
            metrics = result['metrics']
            print(f"  📁 {os.path.basename(result['file'])}: "
                  f"{metrics['processing_time']:.1f}s, "
                  f"{metrics['mb_per_second']:.1f} MB/s")
        
        print("="*80)

def main():
    parser = argparse.ArgumentParser(description="Test AudioTrans GPU Performance")
    parser.add_argument("--url", default="http://localhost:8001", help="Base URL del API")
    parser.add_argument("--api-key", default="audio-trans-secret-key-2024", help="API Key")
    parser.add_argument("--test-file", help="Archivo de audio para test individual")
    parser.add_argument("--benchmark", action="store_true", help="Ejecutar suite de benchmarks")
    parser.add_argument("--iterations", type=int, default=1, help="Número de iteraciones para benchmark")
    parser.add_argument("--custom-prompt", help="Prompt personalizado para OpenAI")
    
    args = parser.parse_args()
    
    # Crear tester
    tester = AudioTransGPUTester(args.url, args.api_key)
    
    print("🚀 AudioTrans GPU Performance Tester")
    print("="*50)
    
    # Health check inicial
    health = tester.test_health_check()
    if not health:
        logger.error("❌ No se pudo conectar al servicio")
        return
    
    # Verificar si GPU está disponible
    gpu_available = health.get('gpu_stats', {}).get('gpu_available', False)
    if not gpu_available:
        logger.warning("⚠️ GPU no detectada - los tests pueden ejecutarse en CPU")
    
    if args.test_file:
        # Test individual
        tester.test_transcription_performance(args.test_file, args.custom_prompt)
    elif args.benchmark:
        # Suite de benchmarks
        test_files = [
            "test_short.m4a",      # 1-2 minutos
            "test_medium.m4a",     # 5-10 minutos
            "test_long.m4a"        # 15-30 minutos
        ]
        tester.benchmark_suite(test_files, args.iterations)
    else:
        logger.info("ℹ️ Usa --test-file para test individual o --benchmark para suite completo")
        logger.info("ℹ️ Ejemplo: python test_api_gpu.py --test-file audio.m4a")

if __name__ == "__main__":
    main() 