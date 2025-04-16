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
if os.environ.get("DATABASE_URL"):
    db_url = os.environ.get("DATABASE_URL")
    # Mostrar versión redactada por seguridad
    masked_url = db_url.split("@")[0].split(":")
    masked_url[2] = "********"  # Ocultar contraseña
    masked_url = ":".join(masked_url) + "@" + db_url.split("@")[1]
    print(f"Conectando a Neon PostgreSQL: {masked_url}")
else:
    print("Base de datos no configurada correctamente. Usando SQLite local.")

# Punto de entrada para Vercel
app = main_app
