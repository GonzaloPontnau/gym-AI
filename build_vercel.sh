#!/bin/bash
# Script para construir la aplicación en Vercel

# Instalar dependencias
pip install -r requirements.txt

# Crear carpeta de base de datos si no existe
mkdir -p app/db

# Inicializar base de datos (SQLite)
python -c "
import asyncio
from app.db.database import init_db

async def setup_db():
    await init_db()

asyncio.run(setup_db())
"

echo "Construcción completada con éxito"
