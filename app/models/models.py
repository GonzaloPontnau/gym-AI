from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime
import json

# Crear base para los modelos declarativos
Base = declarative_base()

# Obtener la URL de conexión a la BD desde variables de entorno
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/gym_ai")

# Crear el motor de base de datos asíncrono
engine = create_async_engine(DATABASE_URL, echo=True)

# Crear fábrica de sesiones asíncronas
async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

# Modelo para usuarios
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    routines = relationship("Routine", back_populates="user")

# Modelo para rutinas de entrenamiento
class Routine(Base):
    __tablename__ = "routines"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    routine_data = Column(JSON)  # Almacena la rutina completa como JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    name = Column(String(100))
    
    # Relaciones
    user = relationship("User", back_populates="routines")
    chat_messages = relationship("ChatMessage", back_populates="routine")

# Modelo para mensajes de chat
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    routine_id = Column(Integer, ForeignKey("routines.id"))
    sender = Column(String(20))  # "user" o "assistant"
    content = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    routine = relationship("Routine", back_populates="chat_messages")

# Funciones para interactuar con la base de datos
async def get_db():
    """Proporciona una sesión de base de datos"""
    async with async_session() as session:
        yield session

async def create_tables():
    """Crea todas las tablas en la base de datos"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def save_routine(routine_data, user_id=1, routine_id=None):
    """Guarda o actualiza una rutina en la base de datos"""
    async with async_session() as session:
        if routine_id:
            # Actualizar rutina existente
            stmt = select(Routine).where(Routine.id == routine_id)
            result = await session.execute(stmt)
            routine = result.scalar_one_or_none()
            
            if routine:
                routine.routine_data = routine_data
                routine.updated_at = datetime.now()
                await session.commit()
                return routine_id
            
        # Crear nueva rutina
        routine_name = routine_data.get("routine_name", "Mi Rutina")
        new_routine = Routine(
            user_id=user_id,
            routine_data=routine_data,
            name=routine_name
        )
        session.add(new_routine)
        await session.commit()
        await session.refresh(new_routine)
        return new_routine.id

async def get_routine(routine_id):
    """Obtiene una rutina por ID"""
    async with async_session() as session:
        stmt = select(Routine).where(Routine.id == routine_id)
        result = await session.execute(stmt)
        routine = result.scalar_one_or_none()
        
        if routine:
            return routine.routine_data
        return None

async def save_chat_message(routine_id, sender, content):
    """Guarda un mensaje de chat"""
    async with async_session() as session:
        message = ChatMessage(
            routine_id=routine_id,
            sender=sender,
            content=content
        )
        session.add(message)
        await session.commit()
        return True

async def get_chat_history(routine_id):
    """Obtiene el historial de chat para una rutina"""
    async with async_session() as session:
        stmt = select(ChatMessage).where(
            ChatMessage.routine_id == routine_id
        ).order_by(ChatMessage.timestamp)
        
        result = await session.execute(stmt)
        messages = result.scalars().all()
        
        return [
            {
                "sender": msg.sender,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            } for msg in messages
        ]
