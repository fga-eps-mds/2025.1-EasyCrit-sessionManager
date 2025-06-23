from dotenv import load_dotenv
import os

load_dotenv()
print("DATABASE_URL carregado:", os.getenv("DATABASE_URL"))
