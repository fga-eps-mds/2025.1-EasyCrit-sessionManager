import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .connection_manager import manager
import logging
from datetime import datetime

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.websocket('/ws/sessions/{session_id}/connect/{user_id}')
async def websocket_endpoint(websocket: WebSocket, session_id: str, user_id: int):
  client_id = str(user_id)
  logger.info(f'Attempting to connect user {user_id} to session {session_id}')

  try:
    await manager.connect(websocket, client_id)
    logger.info(f'User {user_id} connected to session {session_id}.')

    await manager.send_personal_message(
      {'type': 'status', 'message': f'Conectado à sessão {session_id} como usuário {user_id}.'}, client_id
    )

    while True:
      data = await websocket.receive_text()
      logger.info(f'Mensagem recebida de user {user_id} na sessão {session_id}: {data}')

      try:
        message_data = json.loads(data)
        message_to_publish = {
          'type': 'chat_message',
          'session_id': session_id,
          'user_id': user_id,
          'content': message_data.get('message', data),
          'timestamp': datetime.utcnow().isoformat(),
        }

      except json.JSONDecodeError:
        logger.warning(f'Mensagem inválida (não é JSON) de user {user_id} na sessão {session_id}: {data}')
        await manager.send_personal_message('Erro: Mensagem deve ser JSON.', client_id)
        continue
      except Exception as e:
        logger.error(
          f'Erro ao processar mensagem recebida de user {user_id} na sessão {session_id}: {e}', exc_info=True
        )
        await manager.send_personal_message(f'Erro ao processar mensagem: {e}', client_id)
        continue

      await manager.publish_message(message_to_publish)

  except WebSocketDisconnect as e:
    logger.info(f'Cliente user {user_id} desconectado da sessão {session_id} com código {e.code}: {e.reason}')
    await manager.disconnect(websocket, client_id)
    await manager.publish_message(
      {'type': 'user_left', 'user_id': user_id, 'session_id': session_id, 'timestamp': datetime.utcnow().isoformat()},
    )
  except Exception as e:
    logger.error(f'Erro inesperado com cliente user {user_id} na sessão {session_id}: {e}', exc_info=True)
    await manager.disconnect(websocket, client_id)
    await manager.publish_message(
      {
        'type': 'error',
        'user_id': user_id,
        'session_id': session_id,
        'message': 'Erro inesperado no servidor.',
        'timestamp': datetime.utcnow().isoformat(),
      },
    )
