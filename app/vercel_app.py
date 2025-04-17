"""
Punto de entrada para despliegue en Vercel
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import sys

# Variables de configuración
DEBUG = True
VERCEL_ENV = True
USE_FALLBACK = True # Usar implementación de respaldo si hay problemas

# Configurar logging avanzado
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vercel_app")
logger.setLevel(logging.DEBUG)

# Registrar información del entorno
logger.info("=== Iniciando GymAI en Vercel ===")
logger.info(f"Directorio actual: {os.getcwd()}")
logger.info(f"Contenido del directorio: {os.listdir('.')}")
logger.info(f"Python path: {sys.path}")

# Asegurar que el directorio raíz del proyecto esté en el path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    logger.info(f"Añadido {project_root} al PYTHONPATH")

# Preparar la aplicación de respaldo en caso de error
fallback_app = FastAPI(title="GymAI - Modo de Emergencia")
templates = Jinja2Templates(directory="templates")

# Configurar rutas básicas para la aplicación de respaldo
@fallback_app.get("/", response_class=HTMLResponse)
async def fallback_root(request: Request):
    """Página de inicio en modo de respaldo"""
    return templates.TemplateResponse("chat_initial.html", {"request": request})

@fallback_app.get("/health")
async def health_check():
    """Endpoint para verificar que la aplicación está funcionando"""
    return {"status": "ok", "mode": "fallback"}

# Intentar montar archivos estáticos
try:
    # Verificar diferentes ubicaciones posibles
    static_dirs = [
        "/tmp/staticfiles",
        "staticfiles",
        "static",
        "../static",
        "./static"
    ]
    
    for static_dir in static_dirs:
        if os.path.exists(static_dir):
            fallback_app.mount("/static", StaticFiles(directory=static_dir), name="static")
            logger.info(f"✅ Archivos estáticos montados desde {static_dir}")
            
            # Listar archivos para debug
            try:
                logger.info(f"Contenido de {static_dir}: {os.listdir(static_dir)}")
                if os.path.exists(f"{static_dir}/css"):
                    logger.info(f"Contenido de {static_dir}/css: {os.listdir(f'{static_dir}/css')}")
            except Exception as e:
                logger.error(f"Error al listar archivos en {static_dir}: {e}")
            
            break
    else:
        logger.warning("⚠️ No se encontró directorio de archivos estáticos")
except Exception as e:
    logger.error(f"❌ Error al montar archivos estáticos: {e}")

# Intentar importar la aplicación principal
try:
    if USE_FALLBACK:
        logger.warning("⚠️ Usando aplicación de respaldo por configuración")
        raise ImportError("Forzando modo de respaldo")
        
    # Importar la app principal
    logger.info("Importando aplicación principal...")
    from app.main import app as main_app
    
    # Si llegamos aquí, la importación fue exitosa
    logger.info("✅ Aplicación principal importada correctamente")
    app = main_app
    
except Exception as e:
    logger.error(f"❌ Error al importar la aplicación principal: {str(e)}")
    import traceback
    logger.error(traceback.format_exc())
    
    # Usar la aplicación de respaldo
    logger.warning("⚠️ Usando aplicación de respaldo debido a errores")
    app = fallback_app
