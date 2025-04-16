#!/bin/bash
# Script para construir la aplicación en Vercel

echo "Usando Python de Vercel..."
# En Vercel, necesitamos usar la ruta completa a los ejecutables
which python
which pip

echo "Instalando dependencias..."
/opt/vercel/python3/bin/python -m pip install -r requirements.txt

echo "Creando directorios para archivos estáticos..."
mkdir -p staticfiles
mkdir -p staticfiles/css
mkdir -p staticfiles/js
mkdir -p staticfiles/img

echo "Copiando archivos estáticos..."
if [ -d "static" ]; then
  cp -r static/* staticfiles/
fi

echo "Generando styles.css en la raíz de staticfiles..."
echo "/* Archivo generado automáticamente para Vercel - $(date) */" > staticfiles/styles.css
if [ -f "static/css/styles.css" ]; then
  cat static/css/styles.css >> staticfiles/styles.css
else
  echo "/* Archivo CSS base no encontrado - creando una versión mínima */" >> staticfiles/styles.css
  echo "/* Contenido original de styles.css */" >> staticfiles/styles.css
fi

echo "Asegurando que css/styles.css también existe..."
mkdir -p staticfiles/css
cp staticfiles/styles.css staticfiles/css/styles.css

echo "Creando archivo de test para verificar que los estáticos funcionan..."
echo "<html><body><h1>Archivos estáticos funcionando</h1></body></html>" > staticfiles/test.html

# Crear carpeta de base de datos si no existe (para desarrollo local)
mkdir -p app/db

# No iniciamos la base de datos aquí porque usaremos Neon en producción
# La inicialización de tablas se hará automáticamente en la primera ejecución

echo "Construcción completada con éxito"
touch staticfiles/.gitkeep

# Listar archivos para debug
echo "Contenido de staticfiles:"
ls -la staticfiles
echo "Contenido de staticfiles/css:"
ls -la staticfiles/css 2>/dev/null || echo "No existe directorio css"
