from fastapi.testclient import TestClient
from app.database.database import create_tables
from .main import app

create_tables()

client = TestClient(app)


def test_create_character_endpoint():
  response = client.post(
    '/characters/',
    json={
      'character_name': 'testcharacter',
      'biography': 'testbiography',
      'player_id': 1,
    },
  )
  assert response.status_code == 201


def test_missing_character_name():
  response = client.post(
    '/characters/',
    json={
      'character_name': ' ',
      'biography': 'testbiography',
      'player_id': 1,
    },
  )
  assert response.status_code == 400
  assert response.json() == {'detail': 'Character name cannot be empty or just whitespace.'}


def test_existent_character():
  client.post(
    '/characters/',
    json={
      'character_name': 'existentcharacter',
      'biography': 'testbiography',
      'player_id': 1,
    },
  )
  response = client.post(
    '/characters/',
    json={
      'character_name': 'existentcharacter',
      'biography': 'testbiography',
      'player_id': 1,
    },
  )
  assert response.status_code == 409
  assert response.json() == {'detail': "A character with the name 'existentcharacter' already exists."}
