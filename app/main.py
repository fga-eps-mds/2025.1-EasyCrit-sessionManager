import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get('/')
def read_root():
  return {'message': 'Bem-vindo à API de controle de sessão!'}
