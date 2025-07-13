from sqlalchemy import create_engine, Column, Integer, Text, text
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
  DATABASE_URL = 'sqlite:///./test.db'
  print(f'AVISO: A variável de ambiente DATABASE_URL não foi definida. Usando "{DATABASE_URL}" como padrão.')

connect_args = {'check_same_thread': False} if 'sqlite' in DATABASE_URL else {}

engine = create_engine(
  DATABASE_URL,
  connect_args=connect_args,
)

SessionLocal = sessionmaker(
  autocommit=False,
  autoflush=False,
  bind=engine,
)

Base = declarative_base()


class Character(Base):
  __tablename__ = 'character'

  character_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
  character_name = Column(Text, index=True, unique=True, nullable=False)
  biography = Column(Text, default=None)
  player_id = Column(Integer, nullable=False)


def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()

def create_tables():
  if 'sqlite' in DATABASE_URL and os.path.exists('./test.db'):
    print('Excluindo arquivo de banco de dados existente: ./test.db')
    os.remove('./test.db')

  try:
    with engine.connect() as connection:
      connection.execute(text('CREATE SCHEMA IF NOT EXISTS session_manager'))
      connection.commit()
      print('Schema "session_manager" criado ou já existe.')
  except Exception as e:
    print(f'Erro ao criar schema "session_manager": {e}')

  try:
    Base.metadata.create_all(bind=engine)
    print('Tabelas do banco de dados criadas (ou já existem).')
  except Exception as e:
    print(f'Erro ao criar tabelas: {e}')
    raise

def get_character_by_name(db_session, character_name: str):
  return db_session.query(Character).filter(Character.character_name == character_name).first()


def create_character(db_session, character_data):
  if get_character_by_name(db_session, character_data.character_name):
    return 'conflict'

  new_character = Character(
    character_name=character_data.character_name, biography=character_data.biography, player_id=character_data.player_id
  )
  db_session.add(new_character)
  db_session.commit()
  db_session.refresh(new_character)
  return new_character
