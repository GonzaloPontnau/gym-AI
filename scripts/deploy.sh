#!/bin/bash

# Script para desplegar GymAI en Render
echo "Preparando despliegue de GymAI en Render..."

# Generar SECRET_KEY
echo "Generando SECRET_KEY..."
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
echo "SECRET_KEY generada: $SECRET_KEY"

# Verificar si existe .env
if [ ! -f .env ]; then
    echo "Creando archivo .env..."
    cp .env .env
    # Reemplazar la clave secreta de ejemplo por la generada
    sed -i "s/genera_una_clave_secreta_aqui/$SECRET_KEY/g" .env
    echo "Archivo .env creado. No olvides configurar tu GEMINI_API_KEY."
else
    echo "El archivo .env ya existe."
    # Actualizar SECRET_KEY en .env existente
    sed -i "s/^SECRET_KEY=.*$/SECRET_KEY=$SECRET_KEY/g" .env
    echo "SECRET_KEY actualizada en .env"
fi

# Verificar configuración de render.yaml
if [ -f render.yaml ]; then
    echo "render.yaml encontrado!"
    echo "Para desplegar en Render:"
    echo "1. Abre https://dashboard.render.com/blueprint/new"
    echo "2. Conecta tu repositorio de GitHub"
    echo "3. Configura la variable de entorno GEMINI_API_KEY"
    echo "4. Configura la variable de entorno SECRET_KEY con: $SECRET_KEY"
    echo "5. Haz clic en 'Apply'"
else
    echo "ERROR: render.yaml no encontrado."
    exit 1
fi

echo "Preparación para despliegue completada." 