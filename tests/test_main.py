from fastapi.testclient import TestClient
from dotenv import load_dotenv
import os
from app.main import app
from app.database.database import create_tables

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env.test'))

create_tables()

client = TestClient(app)


def test_read_root():
  response = client.get('/')
  assert response.status_code == 200
  assert response.json() == {'message': 'Welcome to the EasyCrit Session Manager API! Use /docs to see endpoints.'}


def test_create_campaign():
  response = client.post(
    '/campaigns',
    json={
      'session_name': 'Test Campaign',
      'description': 'A test campaign',
      'map_name': 'Map1',
      'start_date': '2025-07-14',
      'start_time': '2025-07-14T12:00:00',
    },
  )
  assert response.status_code == 201
  data = response.json()
  assert data['session_name'] == 'Test Campaign'
  assert data['map_name'] == 'Map1'
  assert 'session_id' in data


def test_create_campaign_missing_field():
  response = client.post(
    '/campaigns',
    json={
      'description': 'A test campaign',
      'map_name': 'Map1',
      'start_date': '2025-07-14',
      'start_time': '2025-07-14T12:00:00',
    },
  )
  assert response.status_code == 422  # Unprocessable Entity


def test_create_campaign_invalid_date():
  response = client.post(
    '/campaigns',
    json={
      'session_name': 'Invalid Date',
      'description': 'A test campaign',
      'map_name': 'Map1',
      'start_date': 'invalid-date',
      'start_time': '2025-07-14T12:00:00',
    },
  )
  assert response.status_code == 422
