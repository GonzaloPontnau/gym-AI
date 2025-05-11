import pytest
import os
import sys
from fastapi.testclient import TestClient
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Asegurar que podamos importar desde el directorio raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.models.models import Routine, Day, Exercise
from app.db.database import Base

# Crear una base de datos de prueba en memoria
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
def test_client():
    """Cliente de prueba para FastAPI"""
    return TestClient(app)

@pytest.fixture
def event_loop():
    """Crear un bucle de eventos estándar para pruebas"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_db_engine():
    """Crear motor de base de datos para pruebas"""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    
    # Crear todas las tablas
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn))
    
    try:
        yield engine
    finally:
        # Eliminar todas las tablas
        async with engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: Base.metadata.drop_all(sync_conn))
        
        # Cerrar el motor
        await engine.dispose()

@pytest.fixture
async def test_db_session(test_db_engine):
    """Crear sesión de base de datos para pruebas"""
    # Crear una fábrica de sesiones
    TestingSessionLocal = sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Crear una sesión
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture
def sample_routine():
    """Crear una rutina de muestra para pruebas"""
    return Routine(
        id=1,
        user_id=1,
        routine_name="Rutina de prueba",
        days=[
            Day(
                day_name="Lunes",
                focus="Pecho y tríceps",
                exercises=[
                    Exercise(
                        name="Press de banca",
                        sets=3,
                        reps="8-12",
                        rest="60-90 seg",
                        equipment="Barra y banco"
                    ),
                    Exercise(
                        name="Fondos en paralelas",
                        sets=3,
                        reps="8-12",
                        rest="60-90 seg",
                        equipment="Paralelas"
                    )
                ]
            ),
            Day(
                day_name="Miércoles",
                focus="Espalda y bíceps",
                exercises=[
                    Exercise(
                        name="Dominadas",
                        sets=3,
                        reps="8-12",
                        rest="60-90 seg",
                        equipment="Barra de dominadas"
                    ),
                    Exercise(
                        name="Curl de bíceps",
                        sets=3,
                        reps="8-12",
                        rest="60-90 seg",
                        equipment="Mancuernas"
                    )
                ]
            )
        ]
    ) 