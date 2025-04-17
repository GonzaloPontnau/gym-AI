#!/bin/bash
echo "Iniciando GymAI"

# Instalar dependencias
echo "Instalando dependencias..."
pip install -r requirements.txt

# Verificar si se proporcionó un puerto en la variable de entorno PORT
if [ -z "$PORT" ]; then
    echo "No se ha definido la variable PORT, usando 8000 por defecto"
    PORT=8000
fi

# Iniciar la aplicación con parámetros de seguridad adicionales para Gunicorn
echo "Iniciando aplicación en el puerto $PORT con parámetros de seguridad"
exec gunicorn -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT app.main:app \
    --limit-request-line 8190 \
    --limit-request-fields 100 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --timeout 120