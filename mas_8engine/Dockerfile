#Dockerfile para el Backend MAS-8ENGINE v2.0
FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /lib/apt/lists/*

# Copiar archivos de dependencias
COPY pyproject.toml .
COPY .venv .venv

# Copiar código fuente
COPY . .

ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["python", "main.py"]
