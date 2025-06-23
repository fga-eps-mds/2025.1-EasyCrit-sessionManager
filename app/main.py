from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from app.database.database import get_db, create_tables, \
    Character as DBCharacter, \
    create_character as create_character_db

app = FastAPI()

origins = "*"

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

class PlayerCreate(BaseModel):
    player_name: str = Field(..., min_length=3, max_length=100)

class PlayerResponse(PlayerCreate):
    player_id: int
    class Config:
        from_attributes = True

@app.on_event("startup")
def on_startup():
    create_tables()

@app.get('/')
def read_root():
    return {'message': 'Welcome to the Character Creation API! Use /docs to see endpoints.'}

@app.post("/players/", response_model=PlayerResponse, status_code=status.HTTP_201_CREATED)
def create_player_endpoint(player_data: PlayerCreate, db: Session = Depends(get_db)):
    existing_player = db.query(DBPlayer).filter(DBPlayer.player_name == player_data.player_name).first()
    if existing_player:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Player with name '{player_data.player_name}' already exists."
        )
    new_player = DBPlayer(player_name=player_data.player_name)
    db.add(new_player)
    db.commit()
    db.refresh(new_player)
    return new_player

@app.post("/characters/", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
def create_character_endpoint(character_data: CharacterCreate, db: Session = Depends(get_db)):
    if not character_data.character_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Character name cannot be empty or just whitespace."
        )
    
    result = create_character_db(db, character_data)
    
    
    if result == "conflict":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A character with the name '{character_data.character_name}' already exists."
        )
    
    return result