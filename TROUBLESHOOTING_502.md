# Solución al Error 502 en Render

## ✅ Problema Identificado y Resuelto

El Error 502 era causado por un conflicto con el bucle de eventos asyncio en `app/main.py`.

### Cambios Realizados

1. **Eliminado el manejo manual del bucle de eventos asyncio** (líneas 13-20 de `app/main.py`)
   - Gunicorn + Uvicorn workers gestionan automáticamente los bucles de eventos
   - El código manual causaba conflictos y errores RuntimeError

## 🔍 Verificación Local (ANTES de desplegar)

**⚡ NUEVO: Script de Diagnóstico Automático**

Antes de desplegar a Render, ejecuta el script de diagnóstico:

```bash
python check_health.py
```

Este script verificará automáticamente:
- ✅ Todas las dependencias están instaladas
- ✅ Variables de entorno configuradas
- ✅ Estructura de archivos correcta
- ✅ La aplicación puede iniciar
- ✅ Conexión a base de datos funciona
- ✅ Configuración de Render es correcta

Si todas las verificaciones pasan, estás listo para desplegar. Si alguna falla, el script te dirá exactamente qué corregir.

---

## 🔍 Verificación del Despliegue en Render

Después de hacer deploy, verifica lo siguiente:

### 1. Variables de Entorno en Render

Asegúrate de que estén configuradas en el Dashboard de Render:

- ✅ `GEMINI_API_KEY`: Tu clave de API de Google Gemini
- ✅ `DATABASE_URL`: `sqlite+aiosqlite:///gym_ai.db` (ya está en render.yaml)
- ✅ `SECRET_KEY`: Una clave secreta generada (opcional pero recomendado)

### 2. Health Check Endpoint

El endpoint `/health` está correctamente implementado en `app/main.py`:

```python
@app.get("/health")
async def health_check():
    """Endpoint para verificar si la aplicación está funcionando"""
    from datetime import datetime
    return {
        "status": "online",
        "server_time": datetime.now().isoformat(),
        "gemini_available": GEMINI_CONFIGURED
    }
```

### 3. Comando de Inicio

El comando en `render.yaml` está optimizado:

```bash
gunicorn -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT app.main:app \
  --limit-request-line 8190 \
  --limit-request-fields 100 \
  --max-requests 1000 \
  --max-requests-jitter 50 \
  --timeout 120
```

## 🚀 Pasos para Desplegar

1. **Hacer commit de los cambios:**
   ```bash
   git add app/main.py TROUBLESHOOTING_502.md
   git commit -m "Fix: Mejorar health check y startup event para diagnosticar Error 502"
   git push origin master
   ```

2. **Render desplegará automáticamente** (si tienes autoDeploy: true)

3. **Verificar el despliegue:**
   - Ve a https://dashboard.render.com
   - Selecciona tu servicio "gymai"
   - Ve a la pestaña "Events" - verás el nuevo deploy
   - Espera a que el estado cambie a "Live" (2-5 minutos)
   - Accede a `https://tu-app.onrender.com/health`
   - Deberías ver: 
     ```json
     {
       "status": "ok",
       "server_time": "2025-10-01T...",
       "gemini_available": true,
       "database": "connected"
     }
     ```

4. **Si el Error 502 persiste después de 5 minutos:**
   - Ve a la pestaña "Logs" en el Dashboard de Render
   - Busca el error específico que está causando el problema
   - Revisa las secciones siguientes según el error encontrado

## 🐛 Si el Error 502 Persiste

### Revisar Logs en Render

1. Ve a tu Dashboard de Render
2. Selecciona tu servicio "gymai"
3. Ve a la pestaña "Logs"
4. Busca errores como:
   - `RuntimeError`
   - `Database error`
   - `ImportError`
   - Problemas con `GEMINI_API_KEY`

### Posibles Causas Adicionales

#### 1. GEMINI_API_KEY no configurada

Si ves en los logs:
```
⚠️ GEMINI_API_KEY no encontrada, servicio de IA no estará disponible
```

**Solución:** Configura la variable de entorno `GEMINI_API_KEY` en Render Dashboard

#### 2. Timeout durante la inicialización

Si ves:
```
Worker timeout
```

**Solución:** Ya está configurado `--timeout 120`, pero puedes aumentarlo en render.yaml:
```yaml
startCommand: gunicorn ... --timeout 180
```

#### 3. Problemas con la base de datos SQLite

En el plan free de Render, el sistema de archivos es efímero. Si necesitas persistencia:

**Opción A:** Usar PostgreSQL externo (recomendado para producción)
- Crear una BD en [Neon](https://neon.tech) o [Render PostgreSQL](https://render.com/docs/databases)
- Actualizar `DATABASE_URL` en las variables de entorno

**Opción B:** Mantener SQLite (los datos se pierden en cada deploy)
- Esto está bien para pruebas

#### 4. Problemas con dependencias

Verifica que todas las dependencias se instalen correctamente:

```bash
# Localmente
pip install -r requirements.txt
```

Si hay errores, actualiza `requirements.txt`

## 📊 Verificación Final

Después del deploy exitoso, prueba:

1. **Página principal:** `https://tu-app.onrender.com/`
2. **Health check:** `https://tu-app.onrender.com/health`
3. **Lista de rutinas:** `https://tu-app.onrender.com/routines`
4. **Crear una rutina:** Usa el formulario en la página principal

## 💡 Mejoras Adicionales Recomendadas

### 1. Mejorar el Health Check

Puedes hacer el health check más robusto verificando la BD:

```python
@app.get("/health")
async def health_check():
    """Endpoint mejorado para verificar salud de la aplicación"""
    from datetime import datetime
    
    # Verificar conexión a BD
    db_status = "unknown"
    try:
        # Intentar una consulta simple
        from app.db.database import engine
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)[:50]}"
    
    return {
        "status": "online",
        "server_time": datetime.now().isoformat(),
        "gemini_available": GEMINI_CONFIGURED,
        "database": db_status
    }
```

### 2. Configurar Logs Estructurados

Agrega logging para facilitar debugging:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

### 3. Monitoreo de Errores

Considera integrar un servicio como [Sentry](https://sentry.io/) para monitorear errores en producción.

## 📞 Soporte

Si el problema persiste después de estos pasos:

1. Revisa los logs completos en Render
2. Verifica que todos los archivos necesarios estén en el repositorio
3. Comprueba que no haya archivos .pyc o __pycache__ que causen conflictos

---

**Última actualización:** 2025-10-01

