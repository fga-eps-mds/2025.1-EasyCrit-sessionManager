from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .connection_manager import manager
import json

router = APIRouter()


@router.websocket('/ws/connect/{client_id}')
async def websocket_endpoint(websocket: WebSocket, client_id: str):
  await manager.connect(websocket, client_id)
  try:
    while True:
      data = await websocket.receive_text()
      try:
        message_data = json.loads(data)

        await manager.send_personal_message(f'Message text was: {message_data}', client_id)

        await manager.broadcast(f'Client {client_id}: {message_data}', exclude=client_id)

      except json.JSONDecodeError:
        await manager.send_personal_message('Error: Invalid JSON', client_id)
  except WebSocketDisconnect:
    manager.disconnect(client_id)
    await manager.broadcast(f'Client {client_id} left the chat')
