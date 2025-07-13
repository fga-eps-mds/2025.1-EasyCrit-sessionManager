import jwt
import os
from jwt import ExpiredSignatureError, InvalidTokenError
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware

# TODO: Use a mesma SECRET_KEY que o serviço de autenticação (2025.1-EasyCrit-auth)
SECRET_KEY = os.getenv(
  'SECRET_KEY', 'your-secret-key'
)  # Use uma chave secreta forte e gerada aleatoriamente em produção

oauth2_scheme = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
  token = credentials.credentials
  try:
    # TODO: Verifique se o SECRET_KEY é o mesmo usado no serviço de autenticação
    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    # Assumindo que o payload contém o user_id no campo 'sub' (subject)
    user_id: str = payload.get('sub')
    if user_id is None:
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido: user_id ('sub') não encontrado no payload",
        headers={'WWW-Authenticate': 'Bearer'},
      )
    # TODO: Opcional: Validar o usuário no banco de dados se necessário
    # Ex: verificar se o user_id existe na sua tabela de usuários
    return user_id  # Retorna o user_id como string

  except ExpiredSignatureError:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail='Token expirado',
      headers={'WWW-Authenticate': 'Bearer'},
    )
  except InvalidTokenError:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail='Token inválido',
      headers={'WWW-Authenticate': 'Bearer'},
    )
  except Exception as e:
    print(f'Erro inesperado na dependência de autenticação: {e}')
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail='Não autorizado',
      headers={'WWW-Authenticate': 'Bearer'},
    )


# Reativar o middleware JWTAuthMiddleware
class JWTAuthMiddleware(BaseHTTPMiddleware):
  def __init__(self, app):
    super().__init__(app)

  async def dispatch(self, request: Request, call_next):
    auth_header = request.headers.get('Authorization')
    if auth_header:
      try:
        scheme, token = auth_header.split()
        if scheme.lower() == 'bearer':
          try:
            # TODO: Use a mesma SECRET_KEY
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_id: str = payload.get('sub')
            if user_id:
              request.state.user_id = user_id
              print(f'Middleware: Usuário {user_id} autenticado e adicionado ao estado.')
            else:
              print("Middleware: Token decodificado, mas user_id ('sub') não encontrado.")

          except (ExpiredSignatureError, InvalidTokenError) as e:
            print(f'Middleware: Falha na decodificação do token ({type(e).__name__}).')
          except Exception as e:
            print(f'Middleware: Erro inesperado ao processar token: {e}')

      except ValueError:
        print('Middleware: Cabeçalho Authorization mal formatado.')
      except Exception as e:
        print(f'Middleware: Erro inesperado ao processar cabeçalho Authorization: {e}')

    response = await call_next(request)
    return response
