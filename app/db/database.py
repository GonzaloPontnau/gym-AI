import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import aiosqlite
from app.models.models import Routine, ChatMessage

# Ruta a la base de datos
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "gym_ai.db")

async def init_db():
    """Inicializa la base de datos"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Crear tabla de rutinas
        await db.execute('''
        CREATE TABLE IF NOT EXISTS routines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            routine_name TEXT NOT NULL,
            user_id INTEGER DEFAULT 1,
            content JSON NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Crear tabla de mensajes de chat
        await db.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            routine_id INTEGER NOT NULL,
            sender TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (routine_id) REFERENCES routines(id)
        )
        ''')
        
        await db.commit()
        print("Base de datos inicializada correctamente")

async def save_routine(routine: Routine, user_id: int = 1, routine_id: Optional[int] = None) -> int:
    """Guarda una rutina en la base de datos"""
    routine_dict = routine.model_dump()
    routine_json = json.dumps(routine_dict)
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        if routine_id is None:
            # Nueva rutina
            cursor = await db.execute(
                '''
                INSERT INTO routines (routine_name, user_id, content)
                VALUES (?, ?, ?)
                ''',
                (routine.routine_name, user_id, routine_json)
            )
            await db.commit()
            return cursor.lastrowid
        else:
            # Actualizar rutina existente
            await db.execute(
                '''
                UPDATE routines 
                SET routine_name = ?, content = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''',
                (routine.routine_name, routine_json, routine_id)
            )
            await db.commit()
            return routine_id

async def get_routine(routine_id: int) -> Optional[Routine]:
    """Obtiene una rutina de la base de datos por su ID"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            '''
            SELECT id, routine_name, user_id, content 
            FROM routines 
            WHERE id = ?
            ''',
            (routine_id,)
        )
        row = await cursor.fetchone()
        
        if row is None:
            return None
        
        # Convertir el JSON a diccionario
        routine_data = json.loads(row['content'])
        
        # Asegurar que el ID esté establecido correctamente
        routine_data['id'] = row['id']
        routine_data['user_id'] = row['user_id']
        
        return Routine.model_validate(routine_data)

async def get_user_routines(user_id: int) -> List[Dict[str, Any]]:
    """Obtiene todas las rutinas de un usuario"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            '''
            SELECT id, routine_name, created_at, updated_at
            FROM routines
            WHERE user_id = ?
            ORDER BY updated_at DESC
            ''',
            (user_id,)
        )
        rows = await cursor.fetchall()
        
        routines = []
        for row in rows:
            routines.append({
                'id': row['id'],
                'routine_name': row['routine_name'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        
        return routines

async def save_chat_message(routine_id: int, sender: str, content: str) -> int:
    """Guarda un mensaje de chat en la base de datos"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            '''
            INSERT INTO chat_messages (routine_id, sender, content)
            VALUES (?, ?, ?)
            ''',
            (routine_id, sender, content)
        )
        await db.commit()
        return cursor.lastrowid

async def get_chat_history(routine_id: int) -> List[ChatMessage]:
    """Obtiene el historial de chat para una rutina específica"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            '''
            SELECT id, routine_id, sender, content, timestamp
            FROM chat_messages
            WHERE routine_id = ?
            ORDER BY timestamp ASC
            ''',
            (routine_id,)
        )
        rows = await cursor.fetchall()
        
        messages = []
        for row in rows:
            message = ChatMessage(
                id=row['id'],
                routine_id=row['routine_id'],
                sender=row['sender'],
                content=row['content'],
                timestamp=row['timestamp']
            )
            messages.append(message)
        
        return messages