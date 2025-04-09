from fastapi import WebSocket
from typing import Dict, List, Any
import json

class ConnectionManager:
    """Gestiona las conexiones WebSocket"""
    
    def __init__(self):
        # Mapeo de routine_id -> lista de conexiones websocket
        self.active_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, routine_id: int):
        """Conecta un nuevo cliente"""
        await websocket.accept()
        if routine_id not in self.active_connections:
            self.active_connections[routine_id] = []
        self.active_connections[routine_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, routine_id: int):
        """Desconecta un cliente"""
        if routine_id in self.active_connections:
            if websocket in self.active_connections[routine_id]:
                self.active_connections[routine_id].remove(websocket)
    
    async def broadcast(self, routine_id: int, message: Any):
        """Envía un mensaje a todos los clientes conectados a una rutina específica"""
        if routine_id in self.active_connections:
            for connection in self.active_connections[routine_id]:
                await connection.send_json(message)