import json
import os
import asyncio
from typing import Dict, Union, Any, Optional

import redis.asyncio as redis
from fastapi import WebSocket
from redis.exceptions import ConnectionError

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))


class ConnectionManager:
  def __init__(self):
    self.active_connections: Dict[str, WebSocket] = {}
    self.redis_client: Optional[redis.Redis] = None
    self.pubsub: Optional[redis.client.PubSub] = None
    self.redis_channel = 'websocket_channel'

  async def connect_redis(self):
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = int(os.getenv('REDIS_PORT', 6379))
    redis_url = f'redis://{redis_host}:{redis_port}'

    try:
      self.redis_client = redis.from_url(redis_url, decode_responses=True)
      await self.redis_client.ping()
      print('Conectado ao Redis com sucesso.')

      self.pubsub = self.redis_client.pubsub()
      await self.pubsub.subscribe(self.redis_channel)
      print(f'Inscrito no canal Redis: {self.redis_channel}')

      asyncio.create_task(self.pubsub_listener())

    except ConnectionError as e:
      print(f'Erro ao conectar ou configurar Redis: {e}')
      self.redis_client = None
      self.pubsub = None

  async def pubsub_listener(self):
    if not self.pubsub:
      print('Pub/Sub não configurado. Listener não iniciado.')
      return

    print('Iniciando listener Pub/Sub...')
    try:
      async for message in self.pubsub.listen():
        if message['type'] == 'message':
          data = message['data']
          print(f'Mensagem recebida do Redis: {data}')
          try:
            msg_data = json.loads(data)
            target_client_id = msg_data.get('client_id')
            message_content = msg_data.get('message')

            if target_client_id and message_content:
              await self.send_personal_message(message_content, target_client_id)
            else:
              await self.broadcast(message_content)
              print(f'Mensagem Redis sem client_id ou content: {msg_data}')

          except json.JSONDecodeError:
            print(f'Erro ao decodificar JSON da mensagem Redis: {data}')
          except Exception as e:
            print(f'Erro ao processar mensagem Redis: {e}')

    except ConnectionError as e:
      print(f'Erro na conexão Pub/Sub do Redis: {e}')
    except Exception as e:
      print(f'Erro inesperado no listener Pub/Sub: {e}')

  async def connect(self, websocket: WebSocket, client_id: str):
    await websocket.accept()
    self.active_connections[client_id] = websocket
    print(f'Cliente {client_id} conectado. Total de conexões: {len(self.active_connections)}')
    await self.send_personal_message({'type': 'status', 'message': 'Conectado ao Session Manager.'}, client_id)

  async def disconnect(self, websocket: WebSocket, client_id: str):
    if client_id in self.active_connections:
      del self.active_connections[client_id]
      print(f'Cliente {client_id} desconectado. Total de conexões: {len(self.active_connections)}')
      await self.broadcast(
        {'type': 'status', 'message': f'Cliente {client_id} desconectou.'},
        exclude_client_id=client_id,
      )

  async def send_personal_message(self, message: Union[str, Dict[str, Any]], client_id: str):
    if client_id in self.active_connections:
      websocket = self.active_connections[client_id]
      try:
        if isinstance(message, dict):
          await websocket.send_json(message)
        else:
          await websocket.send_text(str(message))
          print(f'Mensagem enviada para {client_id}: {message}')
      except RuntimeError as e:
        print(f'Erro ao enviar mensagem para {client_id}: {e}')
        await self.disconnect(websocket, client_id)
      except Exception as e:
        print(f'Erro inesperado ao enviar mensagem para {client_id}: {e}')
        await self.disconnect(websocket, client_id)

  async def broadcast(
    self,
    message: Union[str, Dict[str, Any]],
    exclude_client_id: Optional[str] = None,
  ):
    disconnected_clients = []
    for client_id, websocket in list(self.active_connections.items()):
      if client_id != exclude_client_id:
        try:
          if isinstance(message, dict):
            await websocket.send_json(message)
          else:
            await websocket.send_text(str(message))
        except RuntimeError:
          disconnected_clients.append(client_id)
        except Exception as e:
          print(f'Erro ao transmitir mensagem para {client_id}: {e}')
          disconnected_clients.append(client_id)

    for client_id in disconnected_clients:
      await self.disconnect(self.active_connections[client_id], client_id)

  async def publish_message(self, message: Dict[str, Any]):
    if self.redis_client:
      try:
        await self.redis_client.publish(self.redis_channel, json.dumps(message))
      except ConnectionError as e:
        print(f'Erro ao publicar mensagem no Redis: {e}')
      except Exception as e:
        print(f'Erro inesperado ao publicar mensagem no Redis: {e}')
    else:
      print('Cliente Redis não disponível. Mensagem não publicada. Fazendo broadcast local.')
      await self.broadcast(message)


manager = ConnectionManager()


async def startup_event_redis():
  await manager.connect_redis()


async def shutdown_event_redis():
  if manager.redis_client:
    await manager.redis_client.close()
    print('Conexão Redis fechada.')
  if manager.pubsub:
    await manager.pubsub.unsubscribe(manager.redis_channel)
    await manager.pubsub.close()
    print('Pub/Sub Redis fechado.')
