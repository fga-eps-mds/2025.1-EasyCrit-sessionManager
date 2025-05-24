from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.auth import JWTAuthMiddleware

app = FastAPI()

# adicionar CORS
origins = '*'  # Alterar para dominios específicos em produção

app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=['*'],
  allow_headers=['*'],
)

app.add_middleware(JWTAuthMiddleware)

@app.get('/')
def read_root():
  return {'message': 'Bem vindo à API de controle de sessão!'}
