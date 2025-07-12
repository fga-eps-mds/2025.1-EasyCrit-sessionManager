import json
from fastapi.testclient import TestClient
from dotenv import load_dotenv
import os
from app.main import app

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env.test'))
client = TestClient(app)


def test_websocket_handshake_and_disconnect():
  session_id = 'test_session_handshake'
  user_id = 1
  with client.websocket_connect(f'/ws/sessions/{session_id}/connect/{user_id}') as ws:
    assert ws.client_state == 1


def test_broadcast_between_two_clients_in_same_session():
  session_id = 'test_session_broadcast'
  user_id1 = 1
  user_id2 = 2

  with client.websocket_connect(f'/ws/sessions/{session_id}/connect/{user_id1}') as ws1:
    with client.websocket_connect(f'/ws/sessions/{session_id}/connect/{user_id2}') as ws2:
      payload = {'text': 'hello world from user 1'}
      payload_str = json.dumps(payload)
      ws1.send_text(payload_str)

      try:
        received_msg1_str = ws1.receive_text(timeout=1)
        received_msg1 = json.loads(received_msg1_str)
        print(f'WS1 received: {received_msg1}')
        assert received_msg1['text'] == payload['text']
        assert received_msg1['user_id'] == user_id1
        assert received_msg1['session_id'] == session_id

      except Exception as e:
        assert False, f'Cliente 1 não recebeu a mensagem esperada: {e}'

      try:
        received_msg2_str = ws2.receive_text(timeout=1)
        received_msg2 = json.loads(received_msg2_str)
        print(f'WS2 received: {received_msg2}')
        assert received_msg2['text'] == payload['text']
        assert received_msg2['user_id'] == user_id1
        assert received_msg2['session_id'] == session_id

      except Exception as e:
        assert False, f'Cliente 2 não recebeu a mensagem esperada: {e}'


def test_send_invalid_json_yields_error():
  session_id = 'test_session_badjson'
  user_id = 3
  with client.websocket_connect(f'/ws/sessions/{session_id}/connect/{user_id}') as ws:
    ws.send_text('not-a-json')
    try:
      err = ws.receive_text(timeout=1)
      assert err == 'Erro: Mensagem deve ser JSON.'
    except Exception as e:
      assert False, f'Não recebeu a mensagem de erro esperada: {e}'
