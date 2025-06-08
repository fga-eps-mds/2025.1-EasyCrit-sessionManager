import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_websocket_handshake_and_disconnect():
    with client.websocket_connect("/ws/connect/handshake123") as ws:
        assert ws


def test_send_valid_json_and_personal_message():
    with client.websocket_connect("/ws/connect/sender1") as ws:
        payload = {"foo": "bar"}
        ws.send_text(json.dumps(payload))
        personal = ws.receive_text()
        assert personal == f"Message text was: {payload}"


def test_send_invalid_json_yields_error():
    with client.websocket_connect("/ws/connect/badjson") as ws:
        ws.send_text("not-a-json")
        err = ws.receive_text()
        assert err == "Error: Invalid JSON"


def test_broadcast_between_two_clients():
    with client.websocket_connect("/ws/connect/alice") as ws1:
        with client.websocket_connect("/ws/connect/bob") as ws2:
            payload = {"hello": "world"}
            ws1.send_text(json.dumps(payload))

            msg1 = ws1.receive_text()
            assert msg1 == f"Message text was: {payload}"

            msg2 = ws2.receive_text()
            assert msg2 == f"Client alice: {payload}"
