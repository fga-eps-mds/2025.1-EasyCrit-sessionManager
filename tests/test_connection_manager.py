import pytest
from app.websocket.connection_manager import ConnectionManager


class WebSocketMock:
  def __init__(self):
    self.messages = []
    self.is_connected = False

  async def accept(self):
    self.is_connected = True

  async def send_text(self, message: str):
    self.messages.append(message)

  async def send_json(self, message):
    self.messages.append(message)


@pytest.mark.asyncio
async def test_connected_client():
  manager = ConnectionManager()
  websocket = WebSocketMock()
  await manager.connect(websocket, 'usuario1')
  assert 'usuario1' in manager.active_connections
  assert websocket.is_connected


@pytest.mark.asyncio
async def test_disconect_client():
  manager = ConnectionManager()
  websocket = WebSocketMock()
  await manager.connect(websocket, 'usuario1')
  await manager.disconnect(websocket, 'usuario1')
  assert 'usuario1' not in manager.active_connections


@pytest.mark.asyncio
async def test_personal_message():
  manager = ConnectionManager()
  websocket = WebSocketMock()
  await manager.connect(websocket, 'usuario1')
  await manager.send_personal_message('Olá, usuario1', 'usuario1')
  assert 'Olá' in ''.join(map(str, websocket.messages))
