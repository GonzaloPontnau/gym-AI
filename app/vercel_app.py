from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
import sys

# Asegurar que el directorio raíz del proyecto esté en el path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar la app principal
from app.main import app as main_app

# Configurar montaje de archivos estáticos para Vercel
if os.path.exists("/tmp/staticfiles"):
    main_app.mount("/static", StaticFiles(directory="/tmp/staticfiles"), name="static")
elif os.path.exists("staticfiles"):
    main_app.mount("/static", StaticFiles(directory="staticfiles"), name="static")

# Verificar y mostrar información de la base de datos para debug
if os.environ.get("NEON_DB_URL"):
    print(f"Usando Neon PostgreSQL - URL: {os.environ.get('NEON_DB_URL')[:20]}...")
else:
    print("Usando SQLite local")

# Punto de entrada para Vercel
app = main_app
