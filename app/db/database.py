import sqlite3
import json
import aiosqlite
from datetime import datetime
import os
from app.models.models import Routine, ChatMessage
from typing import List, Optional, Dict, Any

# Ruta a la base de datos SQLite
# En Vercel, necesitamos usar /tmp para almacenamiento temporal
if os.environ.get("VERCEL_ENV"):
    DB_PATH = "/tmp/gymAI.db"
else:
    DB_PATH = "app/db/gymAI.db"

async def init_db():
    """Inicializa la base de datos con las tablas necesarias"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Crear tabla de rutinas
        await db.execute('''
            CREATE TABLE IF NOT EXISTS routines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                routine_name TEXT NOT NULL,
                routine_data TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        ''')
        
        # Crear tabla de mensajes del chat
        await db.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                routine_id INTEGER NOT NULL,
                sender TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                FOREIGN KEY (routine_id) REFERENCES routines (id) ON DELETE CASCADE
            )
        ''')
        
        await db.commit()

async def save_routine(routine: Routine, user_id: int = None, routine_id: int = None) -> int:
    """
    Guarda una rutina en la base de datos.
    Si routine_id es proporcionado, actualiza la rutina existente,
    de lo contrario, crea una nueva rutina.
    """
    now = datetime.now().isoformat()
    routine_data = routine.model_dump_json()
    
    async with aiosqlite.connect(DB_PATH) as db:
        if routine_id:
            # Actualizar rutina existente
            await db.execute(
                "UPDATE routines SET routine_name = ?, routine_data = ?, updated_at = ? WHERE id = ?",
                (routine.routine_name, routine_data, now, routine_id)
            )
            await db.commit()
            return routine_id
        else:
            # Crear nueva rutina
            user_id = user_id or routine.user_id
            cursor = await db.execute(
                "INSERT INTO routines (user_id, routine_name, routine_data, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, routine.routine_name, routine_data, now, now)
            )
            await db.commit()
            return cursor.lastrowid

async def get_routine(routine_id: int) -> Optional[Routine]:
    """Obtiene una rutina por su ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT routine_data FROM routines WHERE id = ?", 
            (routine_id,)
        )
        result = await cursor.fetchone()
        
        if result:
            routine_dict = json.loads(result[0])
            routine_dict["id"] = routine_id
            return Routine.model_validate(routine_dict)
        return None

async def save_chat_message(routine_id: int, sender: str, content: str) -> int:
    """Guarda un mensaje de chat para una rutina específica"""
    now = datetime.now().isoformat()
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO chat_messages (routine_id, sender, content, timestamp) VALUES (?, ?, ?, ?)",
            (routine_id, sender, content, now)
        )
        await db.commit()
        return cursor.lastrowid

async def get_chat_history(routine_id: int) -> List[Dict[str, Any]]:
    """Obtiene el historial de chat para una rutina específica"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT sender, content FROM chat_messages WHERE routine_id = ? ORDER BY timestamp",
            (routine_id,)
        )
        results = await cursor.fetchall()
        return [dict(row) for row in results]

async def get_user_routines(user_id: int) -> List[Dict[str, Any]]:
    """Obtiene todas las rutinas de un usuario específico"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, routine_name, updated_at FROM routines WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,)
        )
        results = await cursor.fetchall()
        return [dict(row) for row in results]

async def delete_routine_from_db(routine_id: int) -> bool:
    """Elimina una rutina y sus mensajes asociados de la base de datos"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM chat_messages WHERE routine_id = ?", (routine_id,))
            await db.execute("DELETE FROM routines WHERE id = ?", (routine_id,))
            await db.commit()
            return True
    except Exception as e:
        print(f"Error al eliminar rutina: {str(e)}")
        return False