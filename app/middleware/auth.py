from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
import os
from fastapi.responses import JSONResponse

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")

class JWTAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.require_auth = [
            ("GET", "/users"),
            ("PUT", "/users"),
            ("PATCH", "/users"),
        ]
        self.security = HTTPBearer()

    async def dispatch(self, request: Request, call_next):
        needs_auth = any(
            request.method == method and request.url.path.startswith(path)
            for method, path in self.require_auth
        )

        if needs_auth:
            try:
                credentials: HTTPAuthorizationCredentials = await self.security(request)
                payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
                request.state.user = payload
            except ExpiredSignatureError:
                return JSONResponse("Expired token", status_code=401)
            except InvalidTokenError:
                return JSONResponse("Invalid token", status_code=401)
            except Exception:
                return JSONResponse("Unauthorizad token", status_code=401)

        return await call_next(request)
