import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .connection_manager import manager

router = APIRouter()


@router.websocket('/ws/sessions/{session_id}/connect/{user_id}')
async def websocket_endpoint(websocket: WebSocket, session_id: str, user_id: int):
  await manager.connect(session_id, websocket)
  try:
    while True:
      data = await websocket.receive_text()
      print(f'Mensagem recebida de user {user_id} na sessão {session_id}: {data}')

      try:
        message_data = json.loads(data)
        message_data['user_id'] = user_id
        message_data['session_id'] = session_id

      except json.JSONDecodeError:
        print(f'Mensagem inválida (não é JSON): {data}')
        await manager.send_personal_message(websocket, 'Erro: Mensagem deve ser JSON.')
        continue
      except Exception as e:
        print(f'Erro ao processar mensagem recebida: {e}')
        await manager.send_personal_message(websocket, f'Erro ao processar mensagem: {e}')
        continue

      await manager.broadcast_global(session_id, message_data)

  except WebSocketDisconnect as e:
    print(f'Cliente user {user_id} desconectado da sessão {session_id} com código {e.code}: {e.reason}')
    manager.disconnect(session_id, websocket)
    await manager.broadcast_global(
      session_id,
      {'type': 'user_left', 'user_id': user_id, 'session_id': session_id},
    )
  except Exception as e:
    print(f'Erro inesperado com cliente user {user_id} na sessão {session_id}: {e}')
    manager.disconnect(session_id, websocket)
    await manager.broadcast_global(
      session_id,
      {
        'type': 'error',
        'user_id': user_id,
        'session_id': session_id,
        'message': 'Erro inesperado no servidor.',
      },
    )
