# 🚀 **AudioTrans GPU - Guía de Deployment en Google Cloud**

Esta guía detalla cómo desplegar AudioTrans con soporte GPU en Google Cloud Platform usando diferentes servicios.

## 📋 **Índice**

1. [Prerrequisitos](#prerrequisitos)
2. [Configuración Inicial](#configuración-inicial)
3. [Opción A: Cloud Run (Recomendado)](#opción-a-cloud-run)
4. [Opción B: Compute Engine con GPU](#opción-b-compute-engine-con-gpu)
5. [Configuración de CI/CD](#configuración-de-cicd)
6. [Monitoreo y Logging](#monitoreo-y-logging)
7. [Optimizaciones de Costos](#optimizaciones-de-costos)
8. [Troubleshooting](#troubleshooting)

---

## 🛠️ **Prerrequisitos**

### **1. Cuenta y Proyecto GCP**
```bash
# Crear proyecto (opcional)
gcloud projects create audiotrans-gpu-project --name="AudioTrans GPU"

# Seleccionar proyecto
gcloud config set project audiotrans-gpu-project

# Habilitar APIs necesarias
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    compute.googleapis.com \
    container.googleapis.com \
    secretmanager.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com
```

### **2. Instalar herramientas**
```bash
# Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Docker (si no está instalado)
# Seguir: https://docs.docker.com/engine/install/

# Opcional: NVIDIA Container Toolkit (para pruebas locales)
# Seguir: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
```

### **3. Configurar autenticación**
```bash
# Autenticar con GCP
gcloud auth login
gcloud auth configure-docker

# Configurar región por defecto
gcloud config set compute/region us-central1
gcloud config set compute/zone us-central1-a
```

---

## ⚙️ **Configuración Inicial**

### **1. Configurar variables de entorno**
```bash
# Variables del proyecto
export PROJECT_ID=$(gcloud config get-value project)
export REGION="us-central1"
export SERVICE_NAME="audiotrans-gpu"

echo "Proyecto: $PROJECT_ID"
echo "Región: $REGION"
```

### **2. Configurar secretos**
```bash
# Crear secreto para OpenAI API Key
echo "tu-openai-api-key-aqui" | gcloud secrets create openai-api-key \
    --replication-policy="automatic" \
    --data-file=-

# Verificar
gcloud secrets list
```

### **3. Preparar repositorio**
```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/AudioTrans.git
cd AudioTrans

# Cambiar a rama GPU
git checkout google-cloud

# Actualizar archivos de configuración
cp env.example .env
# Editar .env con tus configuraciones específicas
```

---

## 🌊 **Opción A: Cloud Run (Recomendado)**

Cloud Run es la opción más simple pero **no soporta GPUs** nativamente. Usar para desarrollo o cargas ligeras.

### **1. Build y push de la imagen**
```bash
# Build usando Cloud Build
gcloud builds submit \
    --config cloudbuild.yaml \
    --substitutions _REGION=$REGION,_WHISPER_MODEL=medium,_MAX_FILE_SIZE=200MB

# O build local
docker build -f Dockerfile.gpu -t gcr.io/$PROJECT_ID/audiotrans-gpu:latest .
docker push gcr.io/$PROJECT_ID/audiotrans-gpu:latest
```

### **2. Desplegar en Cloud Run**
```bash
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/audiotrans-gpu:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 8Gi \
    --cpu 4 \
    --timeout 3600 \
    --concurrency 1 \
    --max-instances 5 \
    --port 8001 \
    --set-env-vars WHISPER_MODEL=medium \
    --set-env-vars MAX_FILE_SIZE=200MB \
    --set-env-vars API_KEY=audio-trans-secret-key-2024 \
    --set-secrets OPENAI_API_KEY=openai-api-key:latest
```

### **3. Verificar deployment**
```bash
# Obtener URL del servicio
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region $REGION \
    --format 'value(status.url)')

echo "Servicio disponible en: $SERVICE_URL"

# Test health check
curl "$SERVICE_URL/health"
```

---

## 🖥️ **Opción B: Compute Engine con GPU**

Para aprovechar completamente las GPUs NVIDIA.

### **1. Verificar disponibilidad de GPUs**
```bash
# Verificar cuotas de GPU en tu proyecto
gcloud compute project-info describe \
    --format="table(quotas.metric,quotas.limit,quotas.usage)" \
    --filter="quotas.metric:GPUS"

# Verificar tipos de GPU disponibles por zona
gcloud compute accelerator-types list \
    --filter="zone:us-central1-a"
```

### **2. Crear instancia con GPU**
```bash
# Crear instancia
gcloud compute instances create audiotrans-gpu-instance \
    --zone=us-central1-a \
    --machine-type=n1-standard-4 \
    --accelerator=type=nvidia-tesla-t4,count=1 \
    --maintenance-policy=TERMINATE \
    --image-family=cos-stable \
    --image-project=cos-cloud \
    --boot-disk-size=50GB \
    --boot-disk-type=pd-standard \
    --metadata-from-file startup-script=startup-script.sh \
    --tags=audiotrans-gpu \
    --scopes=cloud-platform

# Crear regla de firewall
gcloud compute firewall-rules create audiotrans-gpu-firewall \
    --allow=tcp:8001 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=audiotrans-gpu
```

### **3. Script de startup (startup-script.sh)**
```bash
#!/bin/bash

# Instalar NVIDIA drivers
echo "Instalando NVIDIA drivers..."
/opt/deeplearning/install-driver.sh

# Instalar Docker y NVIDIA Container Runtime
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER

# Instalar NVIDIA Container Runtime
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-container-runtime
sudo systemctl restart docker

# Autenticar Docker con GCR
gcloud auth configure-docker

# Ejecutar contenedor
docker run -d \
    --name audiotrans-gpu \
    --restart unless-stopped \
    --gpus all \
    -p 8001:8001 \
    -e API_KEY=audio-trans-secret-key-2024 \
    -e WHISPER_MODEL=medium \
    -e MAX_FILE_SIZE=500MB \
    -v whisper-models:/home/appuser/.cache/whisper \
    gcr.io/PROJECT_ID/audiotrans-gpu:latest

echo "AudioTrans GPU desplegado exitosamente"
```

### **4. Verificar instancia**
```bash
# Verificar estado de la instancia
gcloud compute instances list --filter="name=audiotrans-gpu-instance"

# Obtener IP externa
EXTERNAL_IP=$(gcloud compute instances describe audiotrans-gpu-instance \
    --zone=us-central1-a \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo "Instancia disponible en: http://$EXTERNAL_IP:8001"

# Test health check
curl "http://$EXTERNAL_IP:8001/health"
```

---

## 🔄 **Configuración de CI/CD**

### **1. Configurar Cloud Build triggers**
```bash
# Crear trigger para despliegue automático
gcloud builds triggers create github \
    --repo-name=AudioTrans \
    --repo-owner=tu-usuario \
    --branch-pattern="google-cloud" \
    --build-config=cloudbuild.yaml \
    --substitutions _REGION=$REGION,_WHISPER_MODEL=medium
```

### **2. Pipeline de CI/CD automatizado**

El archivo `cloudbuild.yaml` ya incluye:
- ✅ Build de imagen GPU
- ✅ Push a Container Registry
- ✅ Deployment a Cloud Run
- ✅ Configuración de secretos

---

## 📊 **Monitoreo y Logging**

### **1. Configurar alertas**
```bash
# Crear política de alerta para errores
gcloud alpha monitoring policies create \
    --policy-from-file=monitoring-policy.yaml
```

### **2. Dashboards personalizados**
```bash
# Importar dashboard
gcloud monitoring dashboards create \
    --config-from-file=gpu-dashboard.json
```

### **3. Logs estructurados**
```bash
# Ver logs de Cloud Run
gcloud logs read "resource.type=cloud_run_revision" \
    --filter="resource.labels.service_name=$SERVICE_NAME" \
    --limit=50

# Ver logs de Compute Engine
gcloud logs read "resource.type=compute_instance" \
    --filter="resource.labels.instance_id=audiotrans-gpu-instance" \
    --limit=50
```

---

## 💰 **Optimizaciones de Costos**

### **1. Cloud Run**
```bash
# Configurar auto-scaling agresivo
gcloud run services update $SERVICE_NAME \
    --region $REGION \
    --min-instances 0 \
    --max-instances 3 \
    --concurrency 1
```

### **2. Compute Engine**
```bash
# Usar instancias preemptible (70% de descuento)
gcloud compute instances create audiotrans-gpu-preempt \
    --zone=us-central1-a \
    --machine-type=n1-standard-2 \
    --accelerator=type=nvidia-tesla-t4,count=1 \
    --preemptible \
    --maintenance-policy=TERMINATE

# Programar parada automática
gcloud compute instances add-metadata audiotrans-gpu-instance \
    --zone=us-central1-a \
    --metadata=shutdown-script="docker stop audiotrans-gpu"
```

### **3. Storage optimizado**
```bash
# Usar discos regionales en lugar de zonales
gcloud compute disks create whisper-models-disk \
    --size=20GB \
    --type=pd-standard \
    --region=us-central1
```

---

## 🔧 **Troubleshooting**

### **Problemas Comunes**

#### **Error de cuota de GPU**
```bash
# Verificar cuotas
gcloud compute project-info describe \
    --format="table(quotas.metric,quotas.limit,quotas.usage)" \
    --filter="quotas.metric:NVIDIA"

# Solicitar aumento de cuota en la consola GCP
```

#### **Out of Memory**
```bash
# Monitorear memoria GPU
gcloud compute ssh audiotrans-gpu-instance \
    --zone=us-central1-a \
    --command="nvidia-smi"

# Ajustar configuración
# Cambiar PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:256
```

#### **Container no inicia**
```bash
# Ver logs detallados
docker logs audiotrans-gpu

# Ejecutar en modo debug
docker run -it --gpus all \
    gcr.io/$PROJECT_ID/audiotrans-gpu:latest \
    /bin/bash
```

#### **API lenta**
```bash
# Verificar métricas
gcloud monitoring metrics list \
    --filter="metric.type:run.googleapis.com/container/cpu/utilizations"

# Escalar verticalmente
gcloud run services update $SERVICE_NAME \
    --region $REGION \
    --cpu 8 \
    --memory 16Gi
```

---

## 📝 **Comandos Útiles**

```bash
# Ver información del proyecto
gcloud config list

# Limpiar recursos
gcloud run services delete $SERVICE_NAME --region $REGION
gcloud compute instances delete audiotrans-gpu-instance --zone=us-central1-a

# Backup de configuración
gcloud config configurations export default --file-path=gcp-config-backup.yaml

# Estimación de costos
gcloud billing budgets list
```

---

## 🔗 **Enlaces Útiles**

- [Documentación Cloud Run](https://cloud.google.com/run/docs)
- [GPUs en Compute Engine](https://cloud.google.com/compute/docs/gpus)
- [Precios de GCP](https://cloud.google.com/pricing/calculators)
- [Cuotas y límites](https://cloud.google.com/compute/quotas)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/)

---

## 📞 **Soporte**

Para problemas específicos:
1. Revisar logs: `gcloud logs read`
2. Verificar configuración: `gcloud config list`
3. Test local: `docker run --gpus all`
4. Crear issue en GitHub con logs completos

**¡AudioTrans GPU listo para producción en Google Cloud! 🚀** 