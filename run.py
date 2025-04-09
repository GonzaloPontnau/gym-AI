import uvicorn
import os
import sys

# Asegurar que el directorio actual esté en el PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Configurar opciones de Uvicorn para el desarrollo
    uvicorn.run(
        "app.main:app",
        host="localhost",
        port=8000,
        reload=True,  # Recarga automática cuando se cambian archivos
        log_level="info"
    )