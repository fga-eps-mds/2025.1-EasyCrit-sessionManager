import os

# Use banco temporário em disco para testes
os.environ['DATABASE_URL'] = 'sqlite:///./test_temp.db'

# Remove o banco antes de rodar (apenas antes dos testes)
if os.path.exists('test_temp.db'):
  os.remove('test_temp.db')

from fastapi.testclient import TestClient
from app.database.database import Base, engine
import app.models  # Importa models para registrar todas as tabelas!
from .main import app

# Cria as tabelas no banco temporário
Base.metadata.create_all(bind=engine)

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


# NÃO remova o banco após os testes aqui! Faça isso manualmente ou com fixture/teardown se necessário.
