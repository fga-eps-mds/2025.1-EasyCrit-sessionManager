import asyncio
import json
import os
from typing import Dict, List, Set
import redis.asyncio as redis
from fastapi import WebSocket, WebSocketDisconnect

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))


class ConnectionManager:
  def __init__(self):
    self.active_connections: Dict[str, List[WebSocket]] = {}
    self.redis_client: redis.Redis | None = None
    self.pubsub: redis.client.PubSub | None = None
    self.pubsub_task: asyncio.Task | None = None
    self._subscribed_channels: Set[str] = set()

  async def connect_redis(self):
    try:
      self.redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
      await self.redis_client.ping()
      print(f'Conectado ao Redis em {REDIS_HOST}:{REDIS_PORT}')
      self.pubsub = self.redis_client.pubsub()
      self.pubsub_task = asyncio.create_task(self._redis_listener())
    except redis.exceptions.ConnectionError as e:
      print(f'Erro ao conectar ao Redis em {REDIS_HOST}:{REDIS_PORT}: {e}')
      self.redis_client = None
      self.pubsub = None
      self.pubsub_task = None
    except Exception as e:
      print(f'Erro inesperado ao conectar ao Redis: {e}')
      self.redis_client = None
      self.pubsub = None
      self.pubsub_task = None

  async def disconnect_redis(self):
    if self.pubsub_task:
      self.pubsub_task.cancel()
      try:
        await self.pubsub_task
      except asyncio.CancelledError:
        print('Tarefa de escuta do Redis cancelada.')
      except Exception as e:
        print(f'Erro ao cancelar tarefa do Redis: {e}')

    if self.pubsub:
      if self._subscribed_channels:
        await self.pubsub.unsubscribe(*list(self._subscribed_channels))
        self._subscribed_channels.clear()
      await self.pubsub.close()
      self.pubsub = None
      print('Cliente Pub/Sub do Redis fechado.')

    if self.redis_client:
      await self.redis_client.close()
      self.redis_client = None
      print('Conexão principal com o Redis fechada.')

  async def _redis_listener(self):
    if not self.pubsub:
      print('Pub/Sub não inicializado. Não é possível iniciar o listener.')
      return

    print('Listener do Redis iniciado. Aguardando inscrições...')

    try:
      async for message in self.pubsub.listen():
        if message['type'] == 'message':
          channel = message['channel']
          data = message['data']
          print(f'Mensagem recebida do Redis no canal {channel}: {data}')

          try:
            if channel.startswith('session:'):
              session_id = channel.split(':', 1)[1]
              await self.broadcast_local(session_id, data)
            else:
              print(f'Mensagem recebida em canal Redis inesperado: {channel}')
          except IndexError:
            print(f'Nome de canal Redis inválido: {channel}')
          except Exception as e:
            print(f'Erro ao processar mensagem do Redis: {e}')

    except asyncio.CancelledError:
      print('Listener do Redis cancelado.')
    except Exception as e:
      print(f'Erro inesperado no listener do Redis: {e}')
    finally:
      print('Finalizando listener do Redis.')

  async def connect(self, session_id: str, websocket: WebSocket):
    await websocket.accept()
    if session_id not in self.active_connections:
      self.active_connections[session_id] = []
      if self.pubsub and f'session:{session_id}' not in self._subscribed_channels:
        await self.pubsub.subscribe(f'session:{session_id}')
        self._subscribed_channels.add(f'session:{session_id}')
        print(f'Inscrito no canal Redis: session:{session_id}')

    self.active_connections[session_id].append(websocket)
    print(
      f'Cliente conectado à sessão {session_id}. Total de conexões para esta sessão: {len(self.active_connections[session_id])}'
    )
    await self.send_personal_message(websocket, f'Conectado à sessão {session_id}')

  def disconnect(self, session_id: str, websocket: WebSocket):
    if session_id in self.active_connections:
      try:
        self.active_connections[session_id].remove(websocket)
        print(f'Cliente desconectado da sessão {session_id}. Restantes: {len(self.active_connections[session_id])}')
        if not self.active_connections[session_id]:
          del self.active_connections[session_id]
          print(f'Nenhuma conexão ativa para a sessão {session_id}. Removendo entrada.')
          if self.pubsub and f'session:{session_id}' in self._subscribed_channels:
            asyncio.create_task(self.pubsub.unsubscribe(f'session:{session_id}'))
            self._subscribed_channels.remove(f'session:{session_id}')
            print(f'Desinscrito do canal Redis: session:{session_id}')

      except ValueError:
        print(f'Erro: WebSocket não encontrado na lista de conexões para a sessão {session_id}.')
      except Exception as e:
        print(f'Erro ao desconectar cliente da sessão {session_id}: {e}')

  async def send_personal_message(self, websocket: WebSocket, message: str):
    try:
      await websocket.send_text(message)
    except WebSocketDisconnect:
      print('Tentativa de enviar mensagem para WebSocket desconectado.')
    except Exception as e:
      print(f'Erro ao enviar mensagem pessoal: {e}')

  async def broadcast_local(self, session_id: str, message: str):
    if session_id in self.active_connections:
      connections_to_send = list(self.active_connections[session_id])
      for connection in connections_to_send:
        try:
          await connection.send_text(message)
        except WebSocketDisconnect:
          print(f'Cliente desconectado durante broadcast local para sessão {session_id}.')

        except Exception as e:
          print(f'Erro ao enviar broadcast local para sessão {session_id}: {e}')

  async def broadcast_global(self, session_id: str, message: any):
    if self.redis_client:
      try:
        message_str = json.dumps(message) if not isinstance(message, str) else message
        channel = f'session:{session_id}'
        await self.redis_client.publish(channel, message_str)
        print(f'Mensagem publicada no Redis canal {channel}: {message_str}')
      except Exception as e:
        print(f'Erro ao publicar mensagem no Redis: {e}')
    else:
      print('Cliente Redis não conectado. Não foi possível publicar a mensagem.')


manager = ConnectionManager()


async def startup_event_redis():
  await manager.connect_redis()


async def shutdown_event_redis():
  await manager.disconnect_redis()
