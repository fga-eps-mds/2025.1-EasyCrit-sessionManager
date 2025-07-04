import os

from dotenv import load_dotenv

load_dotenv()
print('URL:', os.getenv('DATABASE_URL'))
