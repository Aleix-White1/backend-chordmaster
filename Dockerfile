FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias para librosa y audio
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Exponer puerto
EXPOSE 8000

# Comando de inicio con debug
CMD ["sh", "-c", "python debug_env.py && uvicorn main:app --host 0.0.0.0 --port $PORT"]