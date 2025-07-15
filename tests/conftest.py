import os

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
from app.database.database import create_tables
import pytest
from fastapi.testclient import TestClient
from app.main import app


create_tables()


@pytest.fixture
def client():
  return TestClient(app)
