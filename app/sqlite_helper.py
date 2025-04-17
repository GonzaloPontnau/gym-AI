"""
Módulo auxiliar para trabajar con SQLite en modo de desarrollo
cuando las funciones asíncronas fallan en entornos serverless.
"""
import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

def ensure_db_exists():
    """Asegura que el archivo de base de datos SQLite existe y tiene las tablas necesarias"""
    db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "db")
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "gymAI.db")
    
    # Conectar o crear la base de datos
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Crear tablas si no existen
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS routines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        routine_name TEXT NOT NULL,
        routine_data TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL,
        updated_at TIMESTAMP NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        routine_id INTEGER NOT NULL,
        sender TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TIMESTAMP NOT NULL,
        FOREIGN KEY (routine_id) REFERENCES routines (id) ON DELETE CASCADE
    )
    ''')
    
    conn.commit()
    conn.close()
    
    return db_path

def save_routine_sync(routine_dict: Dict[str, Any], user_id: int = None, routine_id: int = None) -> int:
    """Guarda una rutina en SQLite de forma síncrona como fallback"""
    db_path = ensure_db_exists()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    routine_data = json.dumps(routine_dict)
    
    try:
        if routine_id:
            # Actualizar rutina existente
            cursor.execute(
                "UPDATE routines SET routine_name = ?, routine_data = ?, updated_at = ? WHERE id = ?",
                (routine_dict["routine_name"], routine_data, now, routine_id)
            )
            if cursor.rowcount == 0:
                raise ValueError(f"No se encontró rutina con ID {routine_id}")
            result_id = routine_id
        else:
            # Crear nueva rutina
            user_id = user_id or routine_dict.get("user_id", 1)
            cursor.execute(
                "INSERT INTO routines (user_id, routine_name, routine_data, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, routine_dict["routine_name"], routine_data, now, now)
            )
            result_id = cursor.lastrowid
        
        conn.commit()
        return result_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_routine_sync(routine_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene una rutina por su ID de forma síncrona"""
    db_path = ensure_db_exists()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT routine_data FROM routines WHERE id = ?", (routine_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        routine_dict = json.loads(result[0])
        routine_dict["id"] = routine_id
        return routine_dict
    return None

def save_chat_message_sync(routine_id: int, sender: str, content: str) -> int:
    """Guarda un mensaje de chat de forma síncrona"""
    db_path = ensure_db_exists()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    cursor.execute(
        "INSERT INTO chat_messages (routine_id, sender, content, timestamp) VALUES (?, ?, ?, ?)",
        (routine_id, sender, content, now)
    )
    
    message_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return message_id

def get_chat_history_sync(routine_id: int) -> List[Dict[str, Any]]:
    """Obtiene el historial de chat de forma síncrona"""
    db_path = ensure_db_exists()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT sender, content FROM chat_messages WHERE routine_id = ? ORDER BY timestamp",
        (routine_id,)
    )
    
    messages = [{"sender": row[0], "content": row[1]} for row in cursor.fetchall()]
    conn.close()
    
    return messages
