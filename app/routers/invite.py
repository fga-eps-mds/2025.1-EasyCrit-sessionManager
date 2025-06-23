from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime
import os

from app.database.database import get_db
from app.models import Session as GameSession, Invite, UserSession

router = APIRouter()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

def get_current_user_id():
    return "fake-user-id-123"

# INVITE ENDPOINT
@router.get("/api/session/{session_id}/invite")
def create_invite(session_id: str, db: Session = Depends(get_db)):
    session = db.query(GameSession).filter(GameSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    token = str(uuid4())
    invite = Invite(
        token=token,
        session_id=session_id,
        created_at=datetime.utcnow()
    )

    db.add(invite)
    db.commit()
    db.refresh(invite)

    return {
        "invite_api_url": f"http://localhost:8000/invite/{token}",
        "invite_redirect_url": f"http://localhost:8000/invite-redirect/{token}",
        "invite_frontend_url": f"{FRONTEND_URL}/dashboard-player/invite/{token}"
    }

@router.get("/invite/{token}")
def consume_invite(
    token: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    invite = db.query(Invite).filter(Invite.token == token).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Convite inválido")

    existing_link = db.query(UserSession).filter_by(
        user_id=user_id,
        session_id=invite.session_id
    ).first()

    if not existing_link:
        user_session = UserSession(
            user_id=user_id,
            session_id=invite.session_id,
            created_at=datetime.utcnow()
        )
        db.add(user_session)
        db.commit()

    return {
        "message": "Convite consumido com sucesso.",
        "session_id": invite.session_id
    }

@router.get("/invite-redirect/{token}")
def consume_invite_and_redirect(
    token: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    invite = db.query(Invite).filter(Invite.token == token).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Convite inválido")

    existing_link = db.query(UserSession).filter_by(
        user_id=user_id,
        session_id=invite.session_id
    ).first()

    if not existing_link:
        user_session = UserSession(
            user_id=user_id,
            session_id=invite.session_id,
            created_at=datetime.utcnow()
        )
        db.add(user_session)
        db.commit()

    # PAGE REDIRECTION
    return RedirectResponse(url=f"{FRONTEND_URL}/dashboard-player")

# ENDPOINT CREATION OF SESSION AND TEST
@router.post("/api/session/create")
def create_session(db: Session = Depends(get_db)):
    new_session = GameSession(
        name="Sessão de Teste",
        created_at=datetime.utcnow()
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return {
        "message": "Sessão criada com sucesso!",
        "session_id": new_session.id,
        "name": new_session.name
    }
