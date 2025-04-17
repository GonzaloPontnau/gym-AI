"""
Módulo para proporcionar una versión simplificada y funcionalidad mínima
cuando estamos en un entorno serverless o con problemas.
"""
import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional

# Determinar la ubicación de la base de datos SQLite
DB_PATH = "/tmp/gym_ai.db" if os.environ.get("VERCEL") else "app/db/gymAI.db"

def ensure_minimal_db():
    """Crear la base de datos SQLite mínima si no existe"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Crear tablas básicas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS routines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL DEFAULT 1,
        routine_name TEXT NOT NULL,
        routine_data TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        routine_id INTEGER NOT NULL,
        sender TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TEXT NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()
    
    return DB_PATH

def create_demo_routine() -> Dict[str, Any]:
    """Crear una rutina de demostración básica"""
    return {
        "routine_name": "Rutina de Demostración",
        "user_id": 1,
        "days": [
            {
                "day_name": "Lunes",
                "focus": "Pecho y Tríceps",
                "exercises": [
                    {
                        "name": "Flexiones",
                        "sets": 3,
                        "reps": "10-12",
                        "rest": "60 seg",
                        "equipment": "Peso corporal"
                    },
                    {
                        "name": "Fondos en banco",
                        "sets": 3,
                        "reps": "12-15",
                        "rest": "60 seg",
                        "equipment": "Banco"
                    }
                ]
            },
            {
                "day_name": "Miércoles",
                "focus": "Espalda y Bíceps",
                "exercises": [
                    {
                        "name": "Dominadas",
                        "sets": 3,
                        "reps": "8-10",
                        "rest": "90 seg",
                        "equipment": "Barra"
                    },
                    {
                        "name": "Curl de bíceps",
                        "sets": 3,
                        "reps": "10-12",
                        "rest": "60 seg",
                        "equipment": "Mancuernas"
                    }
                ]
            },
            {
                "day_name": "Viernes",
                "focus": "Piernas",
                "exercises": [
                    {
                        "name": "Sentadillas",
                        "sets": 3,
                        "reps": "12-15",
                        "rest": "90 seg",
                        "equipment": "Peso corporal"
                    },
                    {
                        "name": "Zancadas",
                        "sets": 3,
                        "reps": "10 por pierna",
                        "rest": "60 seg",
                        "equipment": "Peso corporal"
                    }
                ]
            }
        ]
    }

def create_demo_routine_in_db() -> int:
    """Crear una rutina de demostración en la base de datos"""
    ensure_minimal_db()
    
    # Datos de la rutina
    routine = create_demo_routine()
    routine_data = json.dumps(routine)
    now = datetime.now().isoformat()
    
    # Guardar en la base de datos
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO routines (user_id, routine_name, routine_data, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (1, routine["routine_name"], routine_data, now, now)
    )
    
    routine_id = cursor.lastrowid
    
    # Añadir mensajes de chat
    cursor.execute(
        "INSERT INTO chat_messages (routine_id, sender, content, timestamp) VALUES (?, ?, ?, ?)",
        (routine_id, "user", "Quiero una rutina para principiantes de 3 días a la semana", now)
    )
    
    cursor.execute(
        "INSERT INTO chat_messages (routine_id, sender, content, timestamp) VALUES (?, ?, ?, ?)",
        (routine_id, "assistant", "¡He creado una rutina básica para ti! Puedes modificarla según tus necesidades.", now)
    )
    
    conn.commit()
    conn.close()
    
    return routine_id

def get_all_routines() -> List[Dict[str, Any]]:
    """Obtener todas las rutinas en modo simple"""
    ensure_minimal_db()
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, routine_name, updated_at FROM routines ORDER BY updated_at DESC")
    
    routines = []
    for row in cursor.fetchall():
        routines.append({
            "id": row["id"],
            "routine_name": row["routine_name"],
            "updated_at": row["updated_at"]
        })
    
    conn.close()
    
    # Si no hay rutinas, crear una de demo
    if not routines:
        routine_id = create_demo_routine_in_db()
        return [{"id": routine_id, "routine_name": "Rutina de Demostración", "updated_at": datetime.now().isoformat()}]
    
    return routines

def get_routine_by_id(routine_id: int) -> Optional[Dict[str, Any]]:
    """Obtener una rutina por su ID"""
    ensure_minimal_db()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT routine_data FROM routines WHERE id = ?", (routine_id,))
    result = cursor.fetchone()
    
    conn.close()
    
    if result:
        routine = json.loads(result[0])
        routine["id"] = routine_id
        return routine
    
    # Si no se encuentra, crear una demo y retornarla
    routine_id = create_demo_routine_in_db()
    return get_routine_by_id(routine_id)
