import os
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError  # Importar para lidar com erros de integridade (ex: duplicidade)

from app.database.database import get_db
from app.models import Invite
from app.models import Session as GameSession  # Renomeado para evitar conflito com Session do SQLAlchemy
from app.models import UserSession
from app.schemas import JoinSessionRequest, JoinSessionResponse  # Importar os schemas
from app.middleware.auth import get_current_user  # Importar a dependência de autenticação

router = APIRouter()

FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')


@router.get('/api/session/{session_id}/invite', tags=['Invites'])
def create_invite(session_id: int, db: Session = Depends(get_db), current_user_id: str = Depends(get_current_user)):
  # TODO: Adicionar lógica para verificar se o current_user_id é o mestre da sessão
  session = db.query(GameSession).filter(GameSession.session_id == session_id).first()  # Usar session_id do modelo
  if not session:
    raise HTTPException(status_code=404, detail='Sessão não encontrada')

  token = str(uuid4())
  # TODO: Adicionar lógica para expiração do convite se necessário
  invite = Invite(token=token, session_id=session_id, created_at=datetime.utcnow())

  try:
    db.add(invite)
    db.commit()
    db.refresh(invite)
  except IntegrityError:
    db.rollback()
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Erro ao gerar convite. Tente novamente.'
    )

  return {
    # TODO: Ajustar URLs se necessário (usar variáveis de ambiente ou configuração)
    'invite_api_url': f'http://localhost:8000/invite/{token}',  # Esta URL consome o convite via API
    'invite_redirect_url': f'http://localhost:8000/invite-redirect/{token}',  # Esta URL consome e redireciona
    'invite_frontend_url': f'{FRONTEND_URL}/dashboard-player?invite_token={token}',  # Sugestão: passar token como query param
  }


# Endpoint para consumir convite via API (pode ser usado internamente ou por outros serviços)
@router.get('/invite/{token}', tags=['Invites'])
def consume_invite(
  token: str,
  db: Session = Depends(get_db),
  user_id: str = Depends(get_current_user),
):
  invite = db.query(Invite).filter(Invite.token == token).first()
  if not invite:
    raise HTTPException(status_code=404, detail='Convite inválido ou expirado')

  existing_link = db.query(UserSession).filter_by(user_id=user_id, session_id=invite.session_id).first()

  if not existing_link:
    user_session = UserSession(user_id=user_id, session_id=invite.session_id, created_at=datetime.utcnow())
    try:
      db.add(user_session)
      db.commit()
      db.refresh(user_session)
    except IntegrityError:
      db.rollback()
      print(f'Aviso: Tentativa de adicionar UserSession duplicado para user {user_id} e session {invite.session_id}')
      pass
    except Exception as e:
      db.rollback()
      print(f'Erro ao criar UserSession: {e}')
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Erro interno ao associar usuário à sessão.'
      )

  return {'message': 'Convite consumido com sucesso.', 'session_id': invite.session_id, 'user_id': user_id}


@router.get('/invite-redirect/{token}', tags=['Invites'])
def consume_invite_and_redirect(
  token: str,
  db: Session = Depends(get_db),
  user_id: str = Depends(get_current_user),
):
  result = consume_invite(token=token, db=db, user_id=user_id)

  # PAGE REDIRECTION
  # TODO: Redirecionar para o dashboard do jogador, talvez passando o session_id ou um indicador de sucesso
  # Exemplo: Redirecionar para o dashboard do jogador com o session_id como query param
  return RedirectResponse(url=f'{FRONTEND_URL}/dashboard-player?session_id={result["session_id"]}')


@router.post('/sessions/join', response_model=JoinSessionResponse, tags=['Sessions'])
async def join_session_by_invite_code(
  request_body: JoinSessionRequest, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)
):
  invite_code = request_body.invite_code.strip()

  # 1. Encontrar o convite pelo código
  invite = db.query(Invite).filter(Invite.token == invite_code).first()
  if not invite:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND, detail='Código de convite inválido ou expirado.'
    )  # TODO: Adicionar verificação de expiração real

  # 2. Verificar se a sessão associada ao convite existe
  session = db.query(GameSession).filter(GameSession.session_id == invite.session_id).first()
  if not session:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Sessão associada ao convite não encontrada.')

  # 3. Associar o usuário à sessão (se ainda não estiver associado)
  existing_link = db.query(UserSession).filter_by(user_id=user_id, session_id=invite.session_id).first()

  if not existing_link:
    user_session = UserSession(user_id=user_id, session_id=invite.session_id, created_at=datetime.utcnow())
    try:
      db.add(user_session)
      db.commit()
      db.refresh(user_session)
      print(f'Usuário {user_id} associado à sessão {invite.session_id} via convite.')
    except IntegrityError:
      db.rollback()
      print(f'Aviso: Tentativa de adicionar UserSession duplicado para user {user_id} e session {invite.session_id}')
      pass
    except Exception as e:
      db.rollback()
      print(f'Erro ao criar UserSession para user {user_id} e session {invite.session_id}: {e}')
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Erro interno ao associar usuário à sessão.'
      )
  else:
    print(f'Usuário {user_id} já estava associado à sessão {invite.session_id}.')

  # 4. Retornar o session_id e user_id conforme esperado pelo frontend
  return {'session_id': invite.session_id, 'user_id': user_id}


# ENDPOINT CREATION OF SESSION TEST (Manter se ainda for útil para testes)
@router.post('/api/session/create', tags=['Sessions'])
def create_session(
  db: Session = Depends(get_db),
  current_user_id: str = Depends(get_current_user),  # Proteger este endpoint também
):
  # TODO: Este endpoint de teste cria uma sessão genérica.
  # Em uma aplicação real, a criação de sessão seria mais complexa,
  # talvez associada a um mestre específico (current_user_id) e com mais detalhes.
  # Considere se este endpoint ainda é necessário ou se deve ser removido/adaptado.
  new_session = GameSession(
    session_name='Sessão de Teste',
    description='Sessão criada para testes.',
    map_name='Mapa Inicial',
    start_date=datetime.utcnow().date(),
    start_time=datetime.utcnow(),
  )
  try:
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    # TODO: Associar o mestre (current_user_id) à sessão recém-criada na tabela UserSession
    # user_session_master = UserSession(user_id=current_user_id, session_id=new_session.session_id, created_at=datetime.utcnow(), is_master=True)
    # db.add(user_session_master)
    # db.commit()

  except Exception as e:
    db.rollback()
    print(f'Erro ao criar sessão de teste: {e}')
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Erro ao criar sessão de teste.')

  return {
    'message': 'Sessão criada com sucesso!',
    'session_id': new_session.session_id,
    'name': new_session.session_name,
  }
