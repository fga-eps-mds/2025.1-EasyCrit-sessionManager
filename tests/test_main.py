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
