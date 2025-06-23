import os

from dotenv import load_dotenv

load_dotenv()
print('DATABASE_URL carregado:', os.getenv('DATABASE_URL'))
