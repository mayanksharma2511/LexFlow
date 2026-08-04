from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.auth import create_access_token
from app.core.config import settings
from app.core.security import verify_password
from app.repositories.user import user_repository


class AuthService:

    def login(
        self,
        db: Session,
        email: str,
        password: str,
    ) -> str | None:

        user = user_repository.get_user_by_email(
            db,
            email,
        )

        if user is None:
            return None

        if not verify_password(
            password,
            user.password_hash,
        ):
            return None

        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "role": user.role,
            },
            expires_delta=timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            ),
        )

        return access_token


auth_service = AuthService()