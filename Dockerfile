# Usar imagen base de Python 3.11 con dependencias del sistema
FROM python:3.11-slim

# Instalar dependencias del sistema para audio y ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY app.py .

# Crear directorio para archivos temporales
RUN mkdir -p /tmp/audiotrans

# Configurar variables de entorno
ENV PYTHONPATH=/app
ENV TEMP_DIR=/tmp/audiotrans

# Exponer puerto
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"] 