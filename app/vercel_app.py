from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
import sys
import importlib.metadata
import asyncio

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

# Inicializar la base de datos explícitamente para entorno Vercel
print("Inicializando base de datos para Vercel...")
try:
    from app.db.database import init_db
    
    # Ejecutar la inicialización de la base de datos
    # Nota: asyncio.run() no funciona en algunos entornos de Vercel, usamos un enfoque alternativo
    async def setup_db():
        print("⏳ Creando tablas en la base de datos...")
        await init_db()
        print("✅ Inicialización de base de datos completada")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup_db())
    loop.close()
    
    print("✅ Base de datos inicializada correctamente")
except Exception as e:
    print(f"❌ Error al inicializar la base de datos: {str(e)}")
    import traceback
    print(traceback.format_exc())

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

# Configurar montaje de archivos estáticos para Vercel - MEJORADO
# Vercel pone los archivos estáticos generados en /tmp/staticfiles en producción
if os.path.exists("/tmp/staticfiles"):
    main_app.mount("/static", StaticFiles(directory="/tmp/staticfiles"), name="static")
    print("✅ Archivos estáticos montados desde /tmp/staticfiles")
    print(f"   Contenido de /tmp/staticfiles: {os.listdir('/tmp/staticfiles')}")
    if os.path.exists("/tmp/staticfiles/css"):
        print(f"   Contenido de /tmp/staticfiles/css: {os.listdir('/tmp/staticfiles/css')}")
elif os.path.exists("staticfiles"):
    main_app.mount("/static", StaticFiles(directory="staticfiles"), name="static")
    print("✅ Archivos estáticos montados desde staticfiles")
else:
    print("⚠️ No se encontró directorio de archivos estáticos")
    # Intentar directorio estático fallback para debug
    if os.path.exists("static"):
        main_app.mount("/static", StaticFiles(directory="static"), name="static")
        print("✅ Fallback: Archivos estáticos montados desde 'static'")

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
