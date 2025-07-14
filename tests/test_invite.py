import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import Invite, Session as GameSession
from app.database.database import get_db
from datetime import datetime
from uuid import uuid4


@pytest.fixture
def client():
  return TestClient(app)


@pytest.fixture
def db_session():
  db = next(get_db())
  yield db
  db.close()


@pytest.fixture
def fake_user_token():
  # Gera um JWT válido para o user_id 'test-user' (ajuste conforme seu auth)
  import jwt

  SECRET_KEY = 'your-secret-key'
  token = jwt.encode({'sub': 'test-user'}, SECRET_KEY, algorithm='HS256')
  return token


@pytest.fixture
def create_session_and_invite(db_session):
  # Cria uma sessão e um convite válido
  session = GameSession(
    session_name='Sessão Teste',
    description='desc',
    map_name='mapa',
    start_date=datetime.utcnow().date(),
    start_time=datetime.utcnow(),
  )
  db_session.add(session)
  db_session.commit()
  db_session.refresh(session)
  invite = Invite(token=str(uuid4()), session_id=session.session_id, created_at=datetime.utcnow())
  db_session.add(invite)
  db_session.commit()
  db_session.refresh(invite)
  return session, invite


def test_create_invite(client, create_session_and_invite, fake_user_token):
  session, _ = create_session_and_invite
  headers = {'Authorization': f'Bearer {fake_user_token}'}
  response = client.get(f'/api/session/{session.session_id}/invite', headers=headers)
  assert response.status_code == 200
  data = response.json()
  assert 'invite_api_url' in data
  assert 'invite_redirect_url' in data
  assert 'invite_frontend_url' in data


def test_consume_invite(client, create_session_and_invite, fake_user_token):
  _, invite = create_session_and_invite
  headers = {'Authorization': f'Bearer {fake_user_token}'}
  response = client.get(f'/invite/{invite.token}', headers=headers)
  assert response.status_code == 200
  data = response.json()
  assert data['message'] == 'Convite consumido com sucesso.'
  assert data['session_id'] == invite.session_id
  assert data['user_id'] == 'test-user'


def test_join_session_by_invite_code(client, create_session_and_invite, fake_user_token):
  _, invite = create_session_and_invite
  headers = {'Authorization': f'Bearer {fake_user_token}'}
  payload = {'invite_code': invite.token}
  response = client.post('/sessions/join', json=payload, headers=headers)
  assert response.status_code == 200
  data = response.json()
  assert data['session_id'] == invite.session_id
  assert data['user_id'] == 'test-user'


def test_invalid_invite_token(client, fake_user_token):
  headers = {'Authorization': f'Bearer {fake_user_token}'}
  response = client.get('/invite/invalid-token', headers=headers)
  assert response.status_code == 404
  assert 'Convite inválido ou expirado' in response.text


def test_invalid_join_invite_code(client, fake_user_token):
  headers = {'Authorization': f'Bearer {fake_user_token}'}
  payload = {'invite_code': 'invalid-token'}
  response = client.post('/sessions/join', json=payload, headers=headers)
  assert response.status_code == 404
  assert 'Código de convite inválido ou expirado' in response.text
