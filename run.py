import uvicorn
import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno explícitamente
load_dotenv()

# Asegurar que el directorio actual esté en el PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Imprimir información de ambiente antes de arrancar
print("\n=== Iniciando GymAI en modo desarrollo ===")

# Verificar variables de entorno explícitamente
database_url = os.environ.get("DATABASE_URL")
if database_url:
    print(f"* Variable DATABASE_URL detectada: {database_url[:20]}...")
    
    # Verificar si asyncpg está instalado
    try:
        import asyncpg
        print("* AsyncPG está instalado. Se usará PostgreSQL.")
        
        # Verificar si la URL tiene configuración SSL
        if "sslmode=require" not in database_url:
            print("* ADVERTENCIA: La URL no especifica sslmode=require, que suele ser necesario para Neon DB.")
            
        # Verificar configuración local
        try:
            from app.local_settings import FORCE_SQLITE
            if FORCE_SQLITE:
                print("* NOTA: FORCE_SQLITE está activado en local_settings.py - se usará SQLite en lugar de PostgreSQL")
        except ImportError:
            pass
    except ImportError:
        print("* ADVERTENCIA: DATABASE_URL está definida pero asyncpg no está instalado.")
        print("* Se usará SQLite local. Para usar PostgreSQL, instale asyncpg:")
        print("* pip install asyncpg")
else:
    print("* No se detectó DATABASE_URL. Usando SQLite local para desarrollo.")

# Verificar si hay variables conflictivas en entorno
for key in os.environ:
    if "DB" in key.upper() or "SQL" in key.upper() or "POSTGRES" in key.upper():
        if key != "DATABASE_URL":
            print(f"* Detectada posible variable de entorno conflictiva: {key}")

print("==========================================\n")

if __name__ == "__main__":
    # Configurar opciones de Uvicorn para el desarrollo
    uvicorn.run(
        "app.main:app",
        host="localhost",
        port=8000,
        reload=True,  # Recarga automática cuando se cambian archivos
        log_level="info"
    )