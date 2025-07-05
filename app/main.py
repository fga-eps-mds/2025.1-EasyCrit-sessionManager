import os

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.auth import JWTAuthMiddleware

from fastapi.staticfiles import StaticFiles
from app.websocket import router as websocket_router

from app.database.database import create_tables, get_db
from app.routers import invite
from app import models, schemas
from sqlalchemy.orm import Session

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print("DATABASE_URL carregado:", DATABASE_URL)

# create_tables()

app = FastAPI(
    title="EasyCrit - Session Manager",
    description="Microserviço para gerenciamento de sessões de RPG.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(invite.router)


@app.post(
    "/campaigns",
    response_model=schemas.Campaign,
    status_code=status.HTTP_201_CREATED,
    tags=["Campaigns"],
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
        print(f"Erro ao criar campanha: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao criar a campanha")


app.add_middleware(JWTAuthMiddleware)

# http://127.0.0.1:8000/static/websocket_test.html
app.mount("/static", StaticFiles(directory="static"), name="static")

# includes the router websocket
app.include_router(websocket_router)


@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API de controle de sessão!"}
