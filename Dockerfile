# Dockerfile — Production Container for Ontology Engine v2.0 FastAPI SaaS

FROM python:3.12-slim

# Evitar escritura de bytecode y forzar salida en UTF-8
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=utf-8 \
    PORT=8080

WORKDIR /app

# Instalación de dependencias de sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requerimientos e instalar paquetes de Python
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Descargar modelo de spacy para español
RUN python -m spacy download es_core_news_sm

# Copiar el código fuente completo de la aplicación
COPY . .

# Exponer el puerto del servidor API
EXPOSE 8080

# Health check para orquestadores en la nube (Railway/Render/AWS)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/api/v1/health || exit 1

# Comando de inicio de la API FastAPI
CMD ["python", "run.py", "--api", "--host", "0.0.0.0", "--port", "8080"]
