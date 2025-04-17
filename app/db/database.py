import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode # Importar utilidades de URL

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, MetaData, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import select, delete
from sqlalchemy import pool

from app.models.models import Routine

# Verificar disponibilidad de asyncpg
asyncpg_available = False
try:
    import asyncpg
    asyncpg_available = True
except ImportError:
    print("Módulo asyncpg no disponible, usando SQLite para desarrollo local")

# Intentar importar configuración local
try:
    from app.local_settings import FORCE_SQLITE
except ImportError:
    FORCE_SQLITE = False

# Determinar de forma explícita qué base de datos usar
use_postgres = False
db_url_env = os.environ.get("DATABASE_URL")

# Debugging - mostrar la URL de DB si existe
if db_url_env:
    print(f"DATABASE_URL encontrado en variables de entorno: {db_url_env}...")

# Solo usar PostgreSQL si tenemos DATABASE_URL, asyncpg y no estamos forzando SQLite
if db_url_env and asyncpg_available and not FORCE_SQLITE and db_url_env.startswith("postgres"):
    use_postgres = True

if use_postgres:
    # Usar Neon PostgreSQL en producción (Vercel)
    # Construir la URL base para asyncpg
    temp_url = db_url_env.replace("postgres://", "postgresql+asyncpg://")
    
    # Parsear la URL para quitar sslmode de la query string
    parsed_url = urlparse(temp_url)
    query_params = parse_qs(parsed_url.query)
    query_params.pop('sslmode', None) # Eliminar sslmode si existe
    new_query = urlencode(query_params, doseq=True)
    
    # Reconstruir la URL sin sslmode en la query
    DB_URL = urlunparse(parsed_url._replace(query=new_query))
    
    IS_SQLITE = False
    print("Utilizando PostgreSQL (Neon Database)")
    print(f"URL de conexión (limpia): {DB_URL[:20]}...") # Mostrar URL limpia
else:
    # Si tenemos una URL sqlite en variable de entorno, usarla
    if db_url_env and db_url_env.startswith("sqlite:"):
        print("Utilizando SQLite desde DATABASE_URL")
        
        # Asegurar que la URL tenga el formato correcto para SQLite asíncrono
        if "sqlite+aiosqlite://" not in db_url_env:
            # Primero obtenemos la parte del path
            if "sqlite:///" in db_url_env:
                path = db_url_env.split("sqlite:///")[1]
            elif "sqlite://" in db_url_env:
                path = db_url_env.split("sqlite://")[1]
                if not path.startswith("/"):
                    path = "/" + path
            else:
                path = "gym_ai.db"  # Valor por defecto
            
            # Construir la URL con el driver aiosqlite
            DB_URL = f"sqlite+aiosqlite:///{path}"
            print(f"URL de SQLite ajustada para usar driver asíncrono: {DB_URL}")
        else:
            DB_URL = db_url_env
    else:
        # Usar SQLite en desarrollo local
        DB_DIR = os.path.dirname(os.path.abspath(__file__))
        os.makedirs(DB_DIR, exist_ok=True)  # Crear directorio si no existe
        DB_PATH = os.path.join(DB_DIR, "gymAI.db")
        DB_URL = f"sqlite+aiosqlite:///{DB_PATH}"
        print(f"Utilizando SQLite local para desarrollo: {DB_URL}")
    
    IS_SQLITE = True

# Asegurar que todas las URLs de SQLite usen aiosqlite
if IS_SQLITE and "sqlite+aiosqlite://" not in DB_URL:
    if "sqlite:///" in DB_URL:
        path = DB_URL.split("sqlite:///")[1]
        DB_URL = f"sqlite+aiosqlite:///{path}"
    elif "sqlite://" in DB_URL:
        path = DB_URL.split("sqlite://")[1]
        if not path.startswith("/"):
            path = "/" + path
        DB_URL = f"sqlite+aiosqlite://{path}"
    print(f"URL de SQLite final ajustada: {DB_URL}")

# Configuración del engine según el tipo de base de datos
if IS_SQLITE:
    engine = create_async_engine(DB_URL, echo=False)
else:
    # Para entorno serverless, usar una configuración extremadamente simple
    # sin pool de conexiones para evitar problemas con el contexto de ejecución
    from sqlalchemy.pool import NullPool
    engine = create_async_engine(
        DB_URL,
        echo=False,
        poolclass=NullPool,
        connect_args={"server_settings": {"statement_timeout": "10000"}}
    )

# Simplificar la sesión para minimizar problemas de contexto asíncrono
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# La función get_session se ha modificado para no usar yield
async def get_db_session():
    """Obtener una sesión de base de datos con manejo explícito"""
    session = async_session()
    try:
        return session
    except Exception as e:
        await session.close()
        print(f"Error al crear sesión de base de datos: {str(e)}")
        raise

# Definir base y metadatos
Base = declarative_base()
metadata = MetaData()

# Definir modelos SQL
class RoutineModel(Base):
    __tablename__ = "routines"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    routine_name = Column(String, nullable=False)
    routine_data = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

class ChatMessageModel(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    routine_id = Column(Integer, ForeignKey("routines.id", ondelete="CASCADE"), nullable=False)
    sender = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)

async def table_exists(table_name):
    """Verifica si una tabla existe en la base de datos"""
    try:
        async with engine.begin() as conn:
            insp = await conn.run_sync(lambda sync_conn: inspect(sync_conn))
            return await conn.run_sync(lambda sync_conn: insp.has_table(table_name))
    except Exception as e:
        print(f"Error al verificar si la tabla {table_name} existe: {str(e)}")
        return False

# Modificamos init_db para ser más confiable en entornos serverless
async def init_db():
    """Inicializa la base de datos con las tablas necesarias"""
    try:
        print("🔍 Verificando si las tablas ya existen...")
        routines_exists = await table_exists("routines")
        chat_messages_exists = await table_exists("chat_messages")
        
        if routines_exists and chat_messages_exists:
            print("✅ Las tablas ya existen, omitiendo creación")
            return
        
        print("🔧 Creando tablas en la base de datos...")
        
        # Usar método directo SQL para evitar problemas con los bucles de eventos
        if not IS_SQLITE:
            try:
                print("Usando SQL directo para crear tablas en PostgreSQL...")
                async with engine.connect() as conn:
                    # Crear la tabla routines si no existe
                    if not routines_exists:
                        await conn.execute("""
                        CREATE TABLE IF NOT EXISTS routines (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL,
                            routine_name VARCHAR NOT NULL,
                            routine_data TEXT NOT NULL,
                            created_at TIMESTAMP NOT NULL,
                            updated_at TIMESTAMP NOT NULL
                        )
                        """)
                    
                    # Crear la tabla chat_messages si no existe
                    if not chat_messages_exists:
                        await conn.execute("""
                        CREATE TABLE IF NOT EXISTS chat_messages (
                            id SERIAL PRIMARY KEY,
                            routine_id INTEGER REFERENCES routines(id) ON DELETE CASCADE,
                            sender VARCHAR NOT NULL,
                            content TEXT NOT NULL,
                            timestamp TIMESTAMP NOT NULL
                        )
                        """)
                    
                    await conn.commit()
                print("✅ Tablas creadas correctamente con SQL directo")
                return
            except Exception as e:
                print(f"Error al crear tablas con SQL directo: {str(e)}")
                import traceback
                print(traceback.format_exc())
        
        # Si llegamos aquí, usar el método de SQLAlchemy como respaldo
        async with engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn))
            
        print("✅ Tablas creadas correctamente con SQLAlchemy")
        
    except Exception as e:
        print(f"❌ Error al inicializar la base de datos: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise

# Resto del código sin cambios
# Reemplazamos la implementación de save_routine para evitar problemas de loop
async def save_routine(routine: Routine, user_id: int = None, routine_id: int = None) -> int:
    """Guarda una rutina en la base de datos con mejor manejo de eventos asíncronos."""
    now = datetime.now()
    routine_data = routine.model_dump_json()
    
    # Para entornos serverless, crear una conexión fresca cada vez
    async with async_session() as session:
        try:
            if routine_id:
                # Actualizar rutina existente con SQL directo para evitar problemas de ORM
                if not IS_SQLITE:
                    query = """
                    UPDATE routines SET 
                    routine_name = :routine_name, 
                    routine_data = :routine_data, 
                    updated_at = :updated_at
                    WHERE id = :routine_id RETURNING id
                    """
                    result = await session.execute(
                        query, 
                        {
                            "routine_name": routine.routine_name,
                            "routine_data": routine_data,
                            "updated_at": now,
                            "routine_id": routine_id
                        }
                    )
                    await session.commit()
                    return routine_id
                else:
                    # Mantener el código original para SQLite en desarrollo
                    stmt = select(RoutineModel).where(RoutineModel.id == routine_id)
                    result = await session.execute(stmt)
                    routine_model = result.scalar_one_or_none()
                    if routine_model:
                        routine_model.routine_name = routine.routine_name
                        routine_model.routine_data = routine_data
                        routine_model.updated_at = now
                        await session.commit()
                        return routine_id
                    else:
                        raise ValueError(f"No se encontró rutina con ID {routine_id}")
            else:
                # Crear nueva rutina con SQL directo para PostgreSQL
                user_id = user_id or routine.user_id
                if not IS_SQLITE:
                    query = """
                    INSERT INTO routines 
                    (user_id, routine_name, routine_data, created_at, updated_at) 
                    VALUES (:user_id, :routine_name, :routine_data, :created_at, :updated_at)
                    RETURNING id
                    """
                    result = await session.execute(
                        query, 
                        {
                            "user_id": user_id,
                            "routine_name": routine.routine_name,
                            "routine_data": routine_data,
                            "created_at": now,
                            "updated_at": now
                        }
                    )
                    new_id = result.scalar_one()
                    await session.commit()
                    return new_id
                else:
                    # Mantener el código original para SQLite en desarrollo
                    routine_model = RoutineModel(
                        user_id=user_id,
                        routine_name=routine.routine_name,
                        routine_data=routine_data,
                        created_at=now,
                        updated_at=now
                    )
                    session.add(routine_model)
                    await session.commit()
                    return routine_model.id
        except Exception as e:
            await session.rollback()
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error al guardar rutina en la base de datos: {str(e)}")
            print(f"Detalles del error: {error_trace}")
            
            # Verificar si es un error de conexión
            if "connection" in str(e).lower() or "timeout" in str(e).lower() or "loop" in str(e).lower():
                raise Exception(f"Error de conexión a la base de datos: {str(e)}")
            
            # Verificar si podría ser un error de schema
            if "column" in str(e).lower() or "table" in str(e).lower():
                raise Exception(f"Error de estructura en la base de datos: {str(e)}")
            
            # Error general si no se identifica específicamente
            raise Exception(f"Error al guardar rutina: {str(e)}")

async def get_routine(routine_id: int) -> Optional[Routine]:
    """Obtiene una rutina por su ID"""
    async with async_session() as session:
        stmt = select(RoutineModel).where(RoutineModel.id == routine_id)
        result = await session.execute(stmt)
        routine_model = result.scalar_one_or_none()
        if (routine_model):
            routine_dict = json.loads(routine_model.routine_data)
            routine_dict["id"] = routine_id
            return Routine.model_validate(routine_dict)
        return None

async def save_chat_message(routine_id: int, sender: str, content: str) -> int:
    """Guarda un mensaje de chat para una rutina específica"""
    now = datetime.now()
    
    async with async_session() as session:
        message_model = ChatMessageModel(
            routine_id=routine_id,
            sender=sender,
            content=content,
            timestamp=now
        )
        session.add(message_model)
        await session.commit()
        return message_model.id

async def get_chat_history(routine_id: int) -> List[Dict[str, Any]]:
    """Obtiene el historial de chat para una rutina específica"""
    async with async_session() as session:
        stmt = select(ChatMessageModel).where(ChatMessageModel.routine_id == routine_id).order_by(ChatMessageModel.timestamp)
        result = await session.execute(stmt)
        messages = result.scalars().all()
        
        return [{"sender": msg.sender, "content": msg.content} for msg in messages]

async def get_user_routines(user_id: int) -> List[Dict[str, Any]]:
    """Obtiene todas las rutinas de un usuario específico"""
    async with async_session() as session:
        stmt = select(RoutineModel).where(RoutineModel.user_id == user_id).order_by(RoutineModel.updated_at.desc())
        result = await session.execute(stmt)
        routines = result.scalars().all()
        
        return [{"id": r.id, "routine_name": r.routine_name, "updated_at": r.updated_at} for r in routines]

async def delete_routine_from_db(routine_id: int) -> bool:
    """Elimina una rutina y sus mensajes asociados de la base de datos"""
    try:
        async with async_session() as session:
            # Eliminar rutina (los mensajes asociados se eliminarán por CASCADE)
            stmt = delete(RoutineModel).where(RoutineModel.id == routine_id)
            await session.execute(stmt)
            await session.commit()
            return True
    except Exception as e:
        print(f"Error al eliminar rutina: {str(e)}")
        return False