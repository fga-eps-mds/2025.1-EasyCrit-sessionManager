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
from app.websocket import router as websocket_router
from app.websocket.connection_manager import startup_event_redis, shutdown_event_redis
from app import models, schemas

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
  allow_origins=[os.getenv('FRONTEND_URL', 'http://localhost:3000')],
  allow_credentials=True,
  allow_methods=['*'],
  allow_headers=['*'],
)

app.add_middleware(JWTAuthMiddleware)
app.include_router(invite.router)
app.include_router(websocket_router)


class CharacterBase(BaseModel):
  character_name: str = Field(..., min_length=1, max_length=100)
  biography: Optional[str] = Field(None, max_length=1000)
  player_id: int = Field(..., gt=0)


@app.post(
  '/campaigns',
  response_model=schemas.Campaign,
  status_code=status.HTTP_201_CREATED,
  tags=['Campaigns'],
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


@app.get('/')
def read_root():
  return {'message': 'Welcome to the EasyCrit Session Manager API! Use /docs to see endpoints.'}


@app.post(
  '/characters/',
  response_model=CharacterResponse,
  status_code=status.HTTP_201_CREATED,
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
