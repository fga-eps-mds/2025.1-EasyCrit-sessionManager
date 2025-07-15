from fastapi.testclient import TestClient
from app.main import app


def test_conection_websocket():
  client = TestClient(app)
  session_id = 'testsession'
  user_id = 1
  with client.websocket_connect(f'/ws/sessions/{session_id}/connect/{user_id}') as websocket:
    websocket.send_text('conecting')
    reply = websocket.receive_text()
    assert reply is not None
    assert len(reply) > 0


def test_message_websocket():
  client = TestClient(app)
  session_id = 'testsession2'
  user_id = 2
  with client.websocket_connect(f'/ws/sessions/{session_id}/connect/{user_id}') as websocket:
    websocket.send_json({'message': 'Message test'})
    reply = websocket.receive_text()
    assert 'message' in reply.lower()
