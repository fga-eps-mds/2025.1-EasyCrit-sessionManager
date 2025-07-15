from sqlalchemy import create_engine, Column, Integer, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
import os

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
  # Using a temporary path to a database during tests
  DATABASE_URL = f'sqlite:///{os.getcwd()}/test.db'
  print(f'WARN: The DATABASE_URL environment variable was not found. Using "{DATABASE_URL}" as the default url.')

connect_args = {'check_same_thread': False} if 'sqlite' in DATABASE_URL else {}

# If the databse is stored in memory (sqlite) don't try to remove the file
if 'sqlite' in DATABASE_URL and ':memory:' in DATABASE_URL:
  engine = create_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False},
    poolclass=StaticPool,
  )
else:
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
  # Will only remove the .db file if the database is sotred on memory (sqlite)
  if 'sqlite' in DATABASE_URL and os.path.exists('./test.db') and ':memory:' not in DATABASE_URL:
    print('Removing .db file: ./test.db')
    os.remove('./test.db')
  try:
    Base.metadata.create_all(bind=engine)
    print('Database tables created.')
  except Exception as e:
    print(f'ERROR: Error while creating database tables: {e}')
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
