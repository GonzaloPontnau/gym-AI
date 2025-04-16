from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
import sys
import importlib.metadata

# Imprimir información de paquetes instalados para depuración
print("=== Paquetes instalados ===")
try:
    installed_packages = sorted([f"{pkg.key}=={pkg.version}" for pkg in importlib.metadata.distributions()])
    for pkg in installed_packages:
        print(f"- {pkg}")
except Exception as e:
    print(f"Error al listar paquetes: {e}")
print("=========================")

# Asegurar que el directorio raíz del proyecto esté en el path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Importar la app principal
    from app.main import app as main_app
    print("✅ Aplicación principal importada correctamente")
except Exception as e:
    print(f"❌ Error al importar la aplicación principal: {str(e)}")
    # Crear una aplicación de emergencia
    main_app = FastAPI(title="GymAI - Error de Inicio")
    
    @main_app.get("/")
    async def error_root():
        return {"error": "La aplicación no pudo iniciarse correctamente. Consulta los logs."}

# Configurar montaje de archivos estáticos para Vercel
if os.path.exists("/tmp/staticfiles"):
    main_app.mount("/static", StaticFiles(directory="/tmp/staticfiles"), name="static")
    print("✅ Archivos estáticos montados desde /tmp/staticfiles")
elif os.path.exists("staticfiles"):
    main_app.mount("/static", StaticFiles(directory="staticfiles"), name="static")
    print("✅ Archivos estáticos montados desde staticfiles")
else:
    print("⚠️ No se encontró directorio de archivos estáticos")

# Verificar y mostrar información de la base de datos para debug
if os.environ.get("DATABASE_URL"):
    db_url = os.environ.get("DATABASE_URL")
    # Mostrar versión redactada por seguridad
    masked_url = db_url.split("@")[0].split(":")
    masked_url[2] = "********"  # Ocultar contraseña
    masked_url = ":".join(masked_url) + "@" + db_url.split("@")[1]
    print(f"✅ Conectando a Neon PostgreSQL: {masked_url}")
else:
    print("⚠️ Base de datos no configurada correctamente. Usando SQLite local.")

# Punto de entrada para Vercel
app = main_app
