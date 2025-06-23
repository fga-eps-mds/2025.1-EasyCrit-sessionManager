from sqlalchemy import create_engine, Column, Integer, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./test.db"
    print(f"WARNING: DATABASE_URL environment variable not set. Using {DATABASE_URL} as default.")

engine = create_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False} if "sqlite" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()

class Player(Base):
    __tablename__ = "player"
    player_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    player_name = Column(Text, unique=True, nullable=False)

    characters = relationship("Character", back_populates="owner")

class Character(Base):
    __tablename__ = "character"
    character_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    character_name = Column(Text, index=True, unique=True, nullable=False)
    biography = Column(Text, default=None)
    player_id = Column(Integer, ForeignKey("player.player_id"), nullable=False)

    owner = relationship("Player", back_populates="characters")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    db_path = DATABASE_URL.replace("sqlite:///./", "./")
    if os.path.exists(db_path) and db_path != "./test.db":
        print(f"Deleting existing database file: {db_path}")
        os.remove(db_path)
    
    Base.metadata.create_all(bind=engine)
    print("Database tables created (or already exist).")


def get_player(db_session, player_id: int):
    return db_session.query(Player).filter(Player.player_id == player_id).first()

def get_character_by_name(db_session, character_name: str):
    return db_session.query(Character).filter(Character.character_name == character_name).first()

def create_character(db_session, character_data):
    if not get_player(db_session, character_data.player_id):
        return "player_not_found"

    if get_character_by_name(db_session, character_data.character_name):
        return "conflict"

    new_character = Character(
        character_name=character_data.character_name,
        biography=character_data.biography,
        player_id=character_data.player_id
    )
    db_session.add(new_character)
    db_session.commit()
    db_session.refresh(new_character)
    return new_character
