from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import sys

# Asegurar que el directorio actual esté en el PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar la aplicación principal
from app.main import app as main_app

# Crear un objeto para el despliegue de Vercel
app = main_app

# Definir punto de entrada para Vercel
@app.get("/api/health-check")
async def health_check():
    """Ruta para verificar que la aplicación está funcionando"""
    return {"status": "ok", "message": "GymAI está funcionando correctamente"}

# Manejar función para Vercel serverless
def handler(request, response):
    return app(request, response)
