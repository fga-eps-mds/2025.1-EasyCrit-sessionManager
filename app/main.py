import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.auth import JWTAuthMiddleware

from fastapi.staticfiles import StaticFiles
from app.websocket import router as websocket_router

from app.database.database import create_tables
from app.routers import invite

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
print('DATABASE_URL carregado:', DATABASE_URL)

create_tables()

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=[os.getenv('FRONTEND_URL', 'http://localhost:3000')],
  allow_credentials=True,
  allow_methods=['*'],
  allow_headers=['*'],
)

app.include_router(invite.router)


app.add_middleware(JWTAuthMiddleware)

# http://127.0.0.1:8000/static/websocket_test.html
app.mount('/static', StaticFiles(directory='static'), name='static')

# includes the router websocket
app.include_router(websocket_router)


@app.get('/')
def read_root():
  return {'message': 'Bem-vindo à API de controle de sessão!'}
