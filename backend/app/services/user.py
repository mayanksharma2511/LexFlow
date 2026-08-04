from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.repositories.user import user_repository
from app.schemas.user import UserCreate


class UserService:

    def create_user(
        self,
        db: Session,
        user_data: UserCreate
    ) -> User:

        existing_user = user_repository.get_by_email(
            db,
            user_data.email
        )

        if existing_user:
            raise ValueError("A user with this email already exists.")

        user = User(
            full_name=user_data.full_name,
            email=user_data.email,
            password_hash=hash_password(user_data.password),
        )

        return user_repository.create(db, user)

    def get_all_users(
        self,
        db: Session
    ) -> list[User]:

        return user_repository.get_all(db)

    def get_user(
        self,
        db: Session,
        user_id: str
    ) -> User | None:

        return user_repository.get_by_id(db, user_id)


user_service = UserService()
