import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os
import json

# Ajustar path para importar desde directorio raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Importar el gestor de WebSockets
from app.websocket.manager import ConnectionManager

class TestWebSocketManager:
    """Pruebas para el gestor de conexiones WebSocket"""
    
    @pytest.fixture
    def connection_manager(self):
        """Crear una instancia del gestor de conexiones"""
        return ConnectionManager()
    
    @pytest.fixture
    def mock_websocket(self):
        """Mock para un WebSocket"""
        websocket = MagicMock()
        websocket.send_json = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.client = MagicMock()
        websocket.client.host = "127.0.0.1"
        return websocket
    
    @pytest.mark.asyncio
    async def test_connect_disconnect(self, connection_manager, mock_websocket):
        """Prueba para conectar y desconectar un cliente WebSocket"""
        # Conectar
        await connection_manager.connect(mock_websocket, routine_id=1)
        
        # Verificar que el cliente está en las conexiones activas
        assert mock_websocket in connection_manager.active_connections
        assert len(connection_manager.active_connections) == 1
        assert 1 in connection_manager.routine_connections
        assert mock_websocket in connection_manager.routine_connections[1]
        
        # Desconectar
        await connection_manager.disconnect(mock_websocket, routine_id=1)
        
        # Verificar que el cliente ya no está en las conexiones activas
        assert mock_websocket not in connection_manager.active_connections
        assert len(connection_manager.active_connections) == 0
        assert len(connection_manager.routine_connections[1]) == 0
    
    @pytest.mark.asyncio
    async def test_send_personal_message(self, connection_manager, mock_websocket):
        """Prueba para enviar un mensaje personal a un cliente"""
        # Conectar cliente
        await connection_manager.connect(mock_websocket, routine_id=1)
        
        # Enviar mensaje
        message = {"type": "test", "content": "Mensaje de prueba"}
        await connection_manager.send_personal_message(message, mock_websocket)
        
        # Verificar que se llamó a send_json
        mock_websocket.send_json.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_broadcast_to_routine(self, connection_manager, mock_websocket):
        """Prueba para enviar un mensaje a todos los clientes de una rutina"""
        # Conectar cliente
        await connection_manager.connect(mock_websocket, routine_id=1)
        
        # Crear otro cliente
        mock_websocket2 = MagicMock()
        mock_websocket2.send_json = AsyncMock()
        mock_websocket2.client = MagicMock()
        mock_websocket2.client.host = "127.0.0.2"
        
        # Conectar segundo cliente
        await connection_manager.connect(mock_websocket2, routine_id=1)
        
        # Enviar mensaje a todos los clientes de la rutina 1
        message = {"type": "test", "content": "Mensaje de difusión"}
        await connection_manager.broadcast_to_routine(message, routine_id=1)
        
        # Verificar que se llamó a send_json en ambos clientes
        mock_websocket.send_json.assert_called_once_with(message)
        mock_websocket2.send_json.assert_called_once_with(message)
        
        # Verificar con un cliente en otra rutina
        mock_websocket3 = MagicMock()
        mock_websocket3.send_json = AsyncMock()
        mock_websocket3.client = MagicMock()
        mock_websocket3.client.host = "127.0.0.3"
        
        # Conectar a rutina diferente
        await connection_manager.connect(mock_websocket3, routine_id=2)
        
        # Reiniciar contadores de llamadas
        mock_websocket.send_json.reset_mock()
        mock_websocket2.send_json.reset_mock()
        mock_websocket3.send_json.reset_mock()
        
        # Enviar mensaje solo a la rutina 2
        await connection_manager.broadcast_to_routine(message, routine_id=2)
        
        # Verificar que solo se llamó al cliente de la rutina 2
        mock_websocket.send_json.assert_not_called()
        mock_websocket2.send_json.assert_not_called()
        mock_websocket3.send_json.assert_called_once_with(message) 