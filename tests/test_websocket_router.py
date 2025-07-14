import json
from fastapi.testclient import TestClient
from dotenv import load_dotenv
import os
from app.main import app
import time

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env.test'))
client = TestClient(app)


def test_websocket_handshake_and_disconnect():
  session_id = 'test_session_handshake'
  user_id = 1
  with client.websocket_connect(f'/ws/sessions/{session_id}/connect/{user_id}') as ws:
    ws.send_text(json.dumps({'message': 'hello'}))
    reply = ws.receive_text()
    assert reply is not None
    assert 'Conectado' in reply or 'chat_message' in reply or 'status' in reply


def _wait_for_chat_message(ws, max_tries=3, timeout=2):
  start = time.time()
  for _ in range(max_tries):
    try:
      # Try to receive a message, but break if timeout exceeded
      while True:
        if time.time() - start > timeout:
          raise TimeoutError('Timeout esperando mensagem de chat')
        try:
          msg = ws.receive_text()
          break
        except Exception:
          time.sleep(0.05)
      data = json.loads(msg)
      if 'content' in data:
        return data
    except Exception:
      pass
  raise AssertionError('Não recebeu mensagem de chat esperada (com campo content)')


def test_broadcast_between_two_clients_in_same_session():
  session_id = 'test_session_broadcast'
  user_id1 = 1
  user_id2 = 2

  with client.websocket_connect(f'/ws/sessions/{session_id}/connect/{user_id1}') as ws1:
    with client.websocket_connect(f'/ws/sessions/{session_id}/connect/{user_id2}') as ws2:
      time.sleep(0.2)  # Pequeno delay para garantir que ambos estejam conectados
      payload = {'message': 'hello world from user 1'}
      payload_str = json.dumps(payload)
      ws1.send_text(payload_str)

      try:
        received_msg1 = _wait_for_chat_message(ws1, timeout=2)
        print(f'WS1 received: {received_msg1}')
        assert received_msg1['content'] == payload['message']
        assert received_msg1['user_id'] == user_id1
        assert received_msg1['session_id'] == session_id
      except Exception as e:
        assert False, f'Cliente 1 não recebeu a mensagem esperada: {e}'

      try:
        received_msg2 = _wait_for_chat_message(ws2, timeout=2)
        print(f'WS2 received: {received_msg2}')
        assert received_msg2['content'] == payload['message']
        assert received_msg2['user_id'] == user_id1
        assert received_msg2['session_id'] == session_id
      except Exception as e:
        assert False, f'Cliente 2 não recebeu a mensagem esperada: {e}'


def test_send_invalid_json_yields_error():
  session_id = 'test_session_badjson'
  user_id = 3
  with client.websocket_connect(f'/ws/sessions/{session_id}/connect/{user_id}') as ws:
    ws.send_text('not-a-json')
    found_error = False
    for _ in range(5):
      try:
        msg = ws.receive_text()
        if msg == 'Erro: Mensagem deve ser JSON.':
          found_error = True
          break
      except Exception:
        break
    assert found_error, 'Não recebeu a mensagem de erro esperada.'
