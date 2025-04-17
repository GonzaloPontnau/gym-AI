# GymAI - Asistente Inteligente de Entrenamiento

GymAI es una aplicación web que utiliza IA (Google Gemini) para generar y personalizar rutinas de entrenamiento adaptadas a tus necesidades.

## Características

- Generación de rutinas personalizadas basadas en tus objetivos y nivel
- Chat en tiempo real para modificar rutinas
- Análisis de imágenes de ejercicios para corregir posturas
- Diseño responsive y moderno

## Tecnologías

- Backend: FastAPI, Python 3.9+
- Frontend: HTML, CSS, JavaScript, Bootstrap 5
- IA: Google Gemini API
- Base de datos: SQLite (producción ligera) / PostgreSQL (escalable)
- WebSockets para comunicación en tiempo real

## Despliegue en Render

La aplicación está configurada para ser desplegada fácilmente en Render.

### Método 1: Despliegue directo con Blueprint

1. Crea una cuenta en [Render](https://render.com)
2. Conecta tu repositorio de GitHub
3. Haz clic en "Blueprint" y selecciona este repositorio
4. Render configurará automáticamente el servicio según el archivo `render.yaml`
5. Configura la variable de entorno `GEMINI_API_KEY` con tu clave de API de Gemini

### Método 2: Despliegue manual

1. Crea una cuenta en [Render](https://render.com)
2. Crea un nuevo servicio web
3. Conecta tu repositorio de GitHub
4. Configura las siguientes opciones:
   - **Environment**: Python 3.9
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT app.main:app`
5. Añade la variable de entorno `GEMINI_API_KEY` con tu clave de API de Gemini

## Desarrollo local

1. Clona este repositorio
2. Crea un entorno virtual: `python -m venv venv`
3. Activa el entorno virtual:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Instala las dependencias: `pip install -r requirements.txt`
5. Crea un archivo `.env` basado en `.env` y añade tu clave API de Gemini
6. Ejecuta la aplicación: `uvicorn app.main:app --reload`

## Licencia

MIT
