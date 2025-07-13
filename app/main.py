import os

from typing import Optional
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from app.database.database import (
  get_db,
  create_tables,
  create_character as create_character_db,
)
from app.middleware.auth import JWTAuthMiddleware
from app.routers import invite
from app import models, schemas
from app.websocket import router as websocket_router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):

  print('Iniciando a aplicação e criando tabelas...')
  create_tables()
  await startup_event_redis()
  yield
  print('Finalizando a aplicação.')
  await shutdown_event_redis()


app = FastAPI(
  lifespan=lifespan,
  title='EasyCrit - Session Manager',
  description='Microserviço para gerenciamento de sessões de RPG.',
  version='0.1.0',
)

origins = '*'

app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=['*'],
  allow_headers=['*'],
)

# Adicionar o middleware de autenticação JWT
# Certifique-se de que a ordem dos middlewares e routers está correta.
# O middleware de autenticação é aplicado antes da inclusão dos routers,
# mas a lógica dentro do middleware deve verificar se a rota precisa de autenticação.
app.add_middleware(JWTAuthMiddleware)

# Incluir os routers
app.include_router(invite.router)
app.include_router(websocket_router)

app.include_router(websocket_router)


# TODO: Mova os schemas CharacterBase, CharacterCreate, CharacterResponse para um arquivo schemas/character.py se a lista crescer
class CharacterBase(BaseModel):
  character_name: str = Field(..., min_length=1, max_length=100)
  biography: Optional[str] = Field(None, max_length=1000)
  player_id: int = Field(..., gt=0)


# TODO: Mova o endpoint /campaigns para um router dedicado (ex: routers/campaigns.py)
# TODO: Adicione a dependência de autenticação a este endpoint se ele precisar ser protegido
app.add_middleware(JWTAuthMiddleware)


@app.post(
  '/campaigns',
  response_model=Campaign, # Usar Campaign diretamente
  status_code=status.HTTP_201_CREATED,
  tags=['Campaigns'],
  # dependencies=[Depends(get_current_user)] # Exemplo de como proteger
)
def create_campaign(campaign: schemas.CampaignCreate, db: Session = Depends(get_db)):

  db_campaign = models.Session(**campaign.model_dump())

  try:
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign
  except Exception as e:
    db.rollback()
    print(f'Erro ao criar campanha: {e}')
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail='Ocorreu um erro interno ao criar a campanha.',
    )


class CharacterCreate(CharacterBase):
  pass


class CharacterResponse(CharacterBase):
  character_id: int

  model_config = ConfigDict(from_attributes=True)


# TODO: Mova o endpoint / para um router dedicado (ex: routers/root.py)
@app.get('/')
def read_root():
  return {'message': 'Welcome to the EasyCrit Session Manager API! Use /docs to see endpoints.'}


# TODO: Mova o endpoint /characters/ para um router dedicado (ex: routers/characters.py)
# TODO: Adicione a dependência de autenticação a este endpoint se ele precisar ser protegido
@app.post(
  '/characters/',
  response_model=CharacterResponse,
  status_code=status.HTTP_201_CREATED,
  tags=['Characters'],  # Adicionado tag
  # dependencies=[Depends(get_current_user)] # Exemplo de como proteger
)
def create_character_endpoint(character_data: CharacterCreate, db: Session = Depends(get_db)):
  if not character_data.character_name.strip():
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail='Character name cannot be empty or just whitespace.',
    )

  result = create_character_db(db, character_data)

  if result == 'conflict':
    raise HTTPException(
      status_code=status.HTTP_409_CONFLICT,
      detail=f"A character with the name '{character_data.character_name}' already exists.",
    )

  return result