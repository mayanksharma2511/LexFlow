import logging
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt  # type: ignore[import-untyped]

from app.core.config import settings

logger = logging.getLogger(__name__)


def _secret() -> str:
    """The JWT signing key. Refuses to work without one, so tokens are never signed with an empty key."""
    if not settings.SECRET_KEY:
        raise RuntimeError("SECRET_KEY is not set. Add it to backend/.env (see .env.example).")
    return settings.SECRET_KEY


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, _secret(), algorithm=settings.ALGORITHM)


def decode_access_token(
    token: str,
) -> dict | None:
    """Return the token's payload, or None if it is invalid or expired."""
    try:
        return jwt.decode(token, _secret(), algorithms=[settings.ALGORITHM])
    except JWTError as e:
        logger.info("Rejected access token: %s", type(e).__name__)
        return None
