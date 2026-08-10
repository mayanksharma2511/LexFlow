from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.auth import decode_access_token
from app.database.dependencies import get_db
from app.repositories.user import user_repository

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials

    payload = decode_access_token(token)

    print("========== AUTH DEBUG ==========")
    print("TOKEN RECEIVED:", bool(token))
    print("PAYLOAD:", payload)

    if payload is None:
        print("RESULT: JWT DECODE FAILED")
        print("================================")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )

    user_id = payload.get("sub")

    print("SUB:", user_id)

    if not user_id:
        print("RESULT: NO SUB IN TOKEN")
        print("================================")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )

    user = user_repository.get_by_id(
        db,
        user_id,
    )

    print("USER FOUND:", user is not None)
    print("USER:", user)
    print("================================")

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    return user
