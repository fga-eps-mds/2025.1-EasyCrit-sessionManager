from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.auth import JWTAuthMiddleware

from fastapi.staticfiles import StaticFiles
from app.websocket import router as websocket_router

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

# http://127.0.0.1:8000/static/websocket_test.html
app.mount('/static', StaticFiles(directory='static'), name='static')

# includes the router websocket
app.include_router(websocket_router)


@app.get('/')
def read_root():
  return {'message': 'Bem vindo à API de controle de sessão!'}
