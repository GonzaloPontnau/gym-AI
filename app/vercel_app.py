"""
Punto de entrada minimalista para Vercel
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import sys

# Configuración extremadamente básica
app = FastAPI(title="GymAI - Entrenador Personal")
templates = Jinja2Templates(directory="templates")

# Montar archivos estáticos
for static_dir in ["/tmp/staticfiles", "staticfiles", "static"]:
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
        print(f"Archivos estáticos montados desde: {static_dir}")
        break

# Asegurar que el directorio raíz del proyecto esté en el path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Ruta de inicio (mínima)
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Página de inicio"""
    return templates.TemplateResponse("chat_initial.html", {"request": request})

# Verificación de salud
@app.get("/health")
async def health():
    """Endpoint para verificar que la aplicación está funcionando"""
    return {"status": "ok", "mode": "minimal"}

# Redirigir a la página principal para cualquier otra ruta
@app.get("/{path:path}")
async def catch_all(path: str):
    """Redirigir cualquier otra ruta a la página principal"""
    return RedirectResponse("/")
