from dotenv import load_dotenv
import os

load_dotenv()
print("URL:", os.getenv("DATABASE_URL"))
