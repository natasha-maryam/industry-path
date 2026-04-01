from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.env_config import ensure_backend_env_loaded

try:
    import jwt  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    jwt = None


auth_scheme = HTTPBearer(auto_error=False)


class AuthSettings:
    @staticmethod
    def auth_required() -> bool:
        ensure_backend_env_loaded()
        return os.getenv("PRODUCTION_AUTH_REQUIRED", "false").strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def jwt_secret() -> str:
        ensure_backend_env_loaded()
        return os.getenv("JWT_SECRET", "").strip()

    @staticmethod
    def jwt_algorithm() -> str:
        ensure_backend_env_loaded()
        return os.getenv("JWT_ALGORITHM", "HS256").strip() or "HS256"


class AuthContext(dict):
    @property
    def user_id(self) -> str:
        return str(self.get("sub") or self.get("user_id") or "anonymous")

    @property
    def is_admin(self) -> bool:
        roles = self.get("roles")
        if isinstance(roles, list):
            role_set = {str(item).lower() for item in roles}
            return "admin" in role_set or "internal" in role_set
        role = str(self.get("role") or "").lower()
        return role in {"admin", "internal"}


def _decode_token(token: str) -> dict[str, Any]:
    if jwt is None:
        raise HTTPException(status_code=503, detail="JWT support unavailable. Install PyJWT.")

    secret = AuthSettings.jwt_secret()
    if not secret:
        raise HTTPException(status_code=503, detail="JWT_SECRET is not configured.")

    try:
        payload = jwt.decode(token, secret, algorithms=[AuthSettings.jwt_algorithm()])
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}") from exc

    exp = payload.get("exp")
    if exp is not None:
        try:
            now = int(datetime.now(timezone.utc).timestamp())
            if int(exp) < now:
                raise HTTPException(status_code=401, detail="Token expired")
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=401, detail=f"Invalid exp claim: {exc}") from exc

    return payload if isinstance(payload, dict) else {}


def get_auth_context(credentials: HTTPAuthorizationCredentials | None = Depends(auth_scheme)) -> AuthContext:
    if not AuthSettings.auth_required():
        return AuthContext({"sub": "dev-user", "roles": ["admin"], "auth_mode": "disabled"})

    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    payload = _decode_token(credentials.credentials)
    return AuthContext(payload)


def require_admin(context: AuthContext = Depends(get_auth_context)) -> AuthContext:
    if not context.is_admin:
        raise HTTPException(status_code=403, detail="Admin role required")
    return context
