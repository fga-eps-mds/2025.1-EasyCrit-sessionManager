from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from dotenv import load_dotenv

from app.database.database import get_db, create_tables, create_character as create_character_db

load_dotenv()

app = FastAPI()

origins = '*'

app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=['*'],
  allow_headers=['*'],
)


class CharacterBase(BaseModel):
  character_name: str = Field(..., min_length=1, max_length=100)
  biography: Optional[str] = Field(None, max_length=1000)
  player_id: int = Field(..., gt=0)


class CharacterCreate(CharacterBase):
  pass


class CharacterResponse(CharacterBase):
  character_id: int

  class Config:
    from_attributes = True


@app.on_event('startup')
def on_startup():
  create_tables()


@app.get('/')
def read_root():
  return {'message': 'Welcome to the Character Creation API! Use /docs to see endpoints.'}


@app.post('/characters/', response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
def create_character_endpoint(character_data: CharacterCreate, db: Session = Depends(get_db)):
  if not character_data.character_name.strip():
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST, detail='Character name cannot be empty or just whitespace.'
    )

  result = create_character_db(db, character_data)

  if result == 'conflict':
    raise HTTPException(
      status_code=status.HTTP_409_CONFLICT,
      detail=f"A character with the name '{character_data.character_name}' already exists.",
    )

  return result
