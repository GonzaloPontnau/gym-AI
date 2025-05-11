# Guía de Pruebas para GymAI

Esta guía proporciona información sobre cómo ejecutar y crear pruebas para el proyecto GymAI utilizando pytest.

## Requisitos

Para ejecutar las pruebas, necesitas tener instalados los siguientes paquetes:

```bash
pip install pytest pytest-asyncio httpx pytest-mock pytest-cov
```

Estos paquetes ya están incluidos en el archivo `requirements.txt` del proyecto.

## Estructura de las Pruebas

Las pruebas están organizadas en el directorio `tests/` con la siguiente estructura:

```
tests/
├── __init__.py                 # Inicialización del paquete de pruebas
├── conftest.py                 # Configuración global y fixtures compartidos
├── test_api_endpoints.py       # Pruebas para endpoints de la API
├── test_gemini_service.py      # Pruebas para el servicio de generación de rutinas
├── test_image_analysis_service.py # Pruebas para el servicio de análisis de imágenes
├── test_models.py              # Pruebas para los modelos Pydantic
├── test_models_simple.py       # Pruebas simples para modelos sin dependencias externas
├── test_simple.py              # Pruebas básicas de demostración
├── test_sqlite_helper.py       # Pruebas para funciones de SQLite
└── test_websocket.py           # Pruebas para la gestión de WebSockets
```

## Ejecutar Pruebas

Hay varias formas de ejecutar las pruebas:

### 1. Usando pytest directamente

Para ejecutar todas las pruebas:

```bash
python -m pytest
```

Para ejecutar con detalles:

```bash
python -m pytest -v
```

Para ejecutar un archivo de prueba específico:

```bash
python -m pytest tests/test_models.py -v
```

### 2. Usando el script run_tests.py

Este script proporciona una forma más fácil de ejecutar las pruebas con diferentes opciones:

```bash
# Ejecutar todas las pruebas
python run_tests.py

# Ejecutar solo pruebas simples que no requieren dependencias externas
python run_tests.py --simple

# Generar informe de cobertura
python run_tests.py --coverage

# Ejecutar pruebas en modo verboso
python run_tests.py -v

# Ejecutar pruebas de un módulo específico
python run_tests.py -m models
```

## Generar Informes de Cobertura

Para generar un informe de cobertura:

```bash
python -m pytest --cov=app --cov-report=term --cov-report=html
```

Esto generará un informe en la terminal y un informe HTML en el directorio `htmlcov/`.

## Escribir Nuevas Pruebas

Para añadir nuevas pruebas:

1. Crea un archivo con el prefijo `test_` en el directorio `tests/`
2. Las clases de prueba deben tener el prefijo `Test`
3. Las funciones de prueba deben tener el prefijo `test_`
4. Para pruebas asíncronas, usa el decorador `@pytest.mark.asyncio`

Ejemplo de una prueba simple:

```python
import pytest

def test_ejemplo():
    assert 1 + 1 == 2

class TestEjemplo:
    def test_metodo(self):
        assert "hola".upper() == "HOLA"
```

Ejemplo de una prueba asíncrona:

```python
import pytest

@pytest.mark.asyncio
async def test_ejemplo_asincrono():
    # Código asíncrono
    result = await funcion_asincrona()
    assert result == valor_esperado
```

## Fixtures

Se han definido varios fixtures útiles en `conftest.py`:

- `test_client`: Cliente de prueba para FastAPI
- `test_db_engine`: Motor de base de datos de prueba (SQLite en memoria)
- `test_db_session`: Sesión de base de datos para pruebas
- `sample_routine`: Rutina de muestra para pruebas

Ejemplo de uso:

```python
def test_con_fixture(test_client):
    response = test_client.get("/")
    assert response.status_code == 200
```

## Mocks

Para pruebas que requieren llamadas a servicios externos como Gemini AI, se utilizan mocks:

```python
from unittest.mock import patch, MagicMock

def test_con_mock():
    with patch("modulo.objeto_a_mockear") as mock_obj:
        mock_obj.metodo.return_value = valor_simulado
        # Código de prueba
        assert resultado == valor_esperado
```

## Consejos para Solucionar Problemas

Si encuentras problemas al ejecutar las pruebas:

1. Asegúrate de tener todas las dependencias instaladas
2. Verifica que estás ejecutando los comandos desde el directorio raíz del proyecto
3. Para problemas con imports, asegúrate de que el directorio raíz esté en el PYTHONPATH
4. Si hay problemas con pruebas asíncronas, verifica que estás usando el decorador `@pytest.mark.asyncio`
5. Para mocks complejos, considera usar fixtures específicos 