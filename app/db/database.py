import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import select, delete

from app.models.models import Routine, ChatMessage

# Determinar qué base de datos usar según el entorno
if os.environ.get("NEON_DB_URL"):
    # Usar Neon PostgreSQL en producción (Vercel)
    DB_URL = os.environ.get("NEON_DB_URL").replace("postgres://", "postgresql+asyncpg://")
    IS_SQLITE = False
else:
    # Usar SQLite en desarrollo local
    DB_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(DB_DIR, "gymAI.db")
    DB_URL = f"sqlite+aiosqlite:///{DB_PATH}"
    IS_SQLITE = True

# Crear engine y session
engine = create_async_engine(DB_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

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

async def init_db():
    """Inicializa la base de datos con las tablas necesarias"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def save_routine(routine: Routine, user_id: int = None, routine_id: int = None) -> int:
    """
    Guarda una rutina en la base de datos.
    Si routine_id es proporcionado, actualiza la rutina existente,
    de lo contrario, crea una nueva rutina.
    """
    now = datetime.now()
    routine_data = routine.model_dump_json()
    
    async with async_session() as session:
        if routine_id:
            # Actualizar rutina existente
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
            # Crear nueva rutina
            user_id = user_id or routine.user_id
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

async def get_routine(routine_id: int) -> Optional[Routine]:
    """Obtiene una rutina por su ID"""
    async with async_session() as session:
        stmt = select(RoutineModel).where(RoutineModel.id == routine_id)
        result = await session.execute(stmt)
        routine_model = result.scalar_one_or_none()
        
        if routine_model:
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