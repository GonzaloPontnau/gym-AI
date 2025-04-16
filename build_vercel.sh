#!/bin/bash
# Script para construir la aplicación en Vercel

echo "=== Iniciando construcción de GymAI para Vercel ==="

# Detectar la ubicación de Python
echo "Buscando ejecutable de Python..."
PYTHON_PATH=$(which python3 2>/dev/null || which python 2>/dev/null)
PIP_PATH=$(which pip3 2>/dev/null || which pip 2>/dev/null)

if [ -z "$PYTHON_PATH" ]; then
  echo "❌ No se pudo encontrar el ejecutable de Python"
  # Probar ubicaciones comunes como fallback
  for path in /usr/bin/python3 /usr/local/bin/python3 /opt/python/bin/python3 python3 python; do
    if command -v $path >/dev/null 2>&1; then
      PYTHON_PATH=$path
      echo "✅ Encontrado Python en: $PYTHON_PATH"
      break
    fi
  done
else
  echo "✅ Encontrado Python en: $PYTHON_PATH"
fi

if [ -z "$PIP_PATH" ]; then
  echo "❌ No se pudo encontrar el ejecutable de pip"
  # Si encontramos Python pero no pip, usar Python para ejecutar pip
  if [ ! -z "$PYTHON_PATH" ]; then
    PIP_PATH="$PYTHON_PATH -m pip"
    echo "✅ Usando pip a través de Python: $PIP_PATH"
  fi
else
  echo "✅ Encontrado pip en: $PIP_PATH"
fi

# Intentar instalar dependencias si se encontró Python
if [ ! -z "$PYTHON_PATH" ]; then
  echo "Instalando dependencias con pip..."
  
  # Usar la variable PYTHON_PATH para llamar a pip
  if [[ "$PIP_PATH" == *"-m pip"* ]]; then
    # Si PIP_PATH contiene "-m pip", es porque estamos usando Python para llamar a pip
    $PYTHON_PATH -m pip install -r requirements.txt
  else
    # Si no, usar PIP_PATH directamente
    $PIP_PATH install -r requirements.txt
  fi
  
  # Verificar que Pillow se ha instalado correctamente (solo si Python está disponible)
  echo "Verificando instalación de Pillow..."
  $PYTHON_PATH -c "import PIL; print('✅ Pillow instalado correctamente')" || echo "❌ Error: Pillow no está instalado"
else
  echo "⚠️ No se pudieron instalar dependencias (Python no encontrado)"
fi

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

echo "Construcción completada con éxito"
touch staticfiles/.gitkeep

# Listar archivos para debug
echo "Contenido de staticfiles:"
ls -la staticfiles
echo "Contenido de staticfiles/css:"
ls -la staticfiles/css 2>/dev/null || echo "No existe directorio css"

# Listar paquetes Python instalados
if [ ! -z "$PYTHON_PATH" ]; then
  echo "Paquetes Python instalados:"
  $PYTHON_PATH -m pip list
else
  echo "⚠️ No se pueden listar paquetes Python (Python no encontrado)"
fi

echo "=== Fin de la construcción de GymAI para Vercel ==="
