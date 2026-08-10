from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt  # type: ignore[import-untyped]

from app.core.config import settings


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:

    to_encode = data.copy()

    expire = (
        datetime.now(timezone.utc)
        + (
            expires_delta
            if expires_delta
            else timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        )
    )

    to_encode.update(
        {
            "exp": expire,
        }
    )

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(
    token: str,
) -> dict | None:

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        print("========== JWT DEBUG ==========")
        print("ALGORITHM:", settings.ALGORITHM)
        print("SECRET KEY PRESENT:", bool(settings.SECRET_KEY))
        print("TOKEN LENGTH:", len(token))
        print("PAYLOAD:", payload)
        print("===============================")

        return payload

    except JWTError as e:
        print("========== JWT ERROR ==========")
        print("ERROR TYPE:", type(e).__name__)
        print("ERROR:", str(e))
        print("ALGORITHM:", settings.ALGORITHM)
        print("SECRET KEY PRESENT:", bool(settings.SECRET_KEY))
        print("TOKEN LENGTH:", len(token))
        print("===============================")

        return None
