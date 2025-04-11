from fastapi import WebSocket
from typing import Dict, List, Set, Any

class ConnectionManager:
    """Gestor de conexiones WebSocket"""
    
    def __init__(self):
        # Diccionario que mapea IDs de rutinas a conjuntos de conexiones WebSocket
        self.connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, routine_id: int):
        """Conecta un nuevo cliente WebSocket para una rutina específica"""
        await websocket.accept()
        
        if routine_id not in self.connections:
            self.connections[routine_id] = set()
            
        self.connections[routine_id].add(websocket)

    def disconnect(self, websocket: WebSocket, routine_id: int):
        """Desconecta un cliente WebSocket"""
        if routine_id in self.connections:
            if websocket in self.connections[routine_id]:
                self.connections[routine_id].remove(websocket)
                
            # Si no quedan conexiones para esta rutina, limpiar
            if not self.connections[routine_id]:
                del self.connections[routine_id]

    async def broadcast(self, routine_id: int, message: Any):
        """Envía un mensaje a todos los clientes conectados a una rutina específica"""
        if routine_id in self.connections:
            disconnected = set()
            
            for connection in self.connections[routine_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.add(connection)
                    
            # Limpiar conexiones desconectadas
            for connection in disconnected:
                self.disconnect(connection, routine_id)