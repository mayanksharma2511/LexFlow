from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:

    def get_by_email(
        self,
        db: Session,
        email: str
    ) -> User | None:

        return (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

    # Alias for authentication
    def get_user_by_email(
        self,
        db: Session,
        email: str
    ) -> User | None:
        return self.get_by_email(db, email)

    def get_by_id(
        self,
        db: Session,
        user_id: str
    ) -> User | None:

        return (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

    def get_all(
        self,
        db: Session
    ) -> list[User]:

        return (
            db.query(User)
            .all()
        )

    def create(
        self,
        db: Session,
        user: User
    ) -> User:

        db.add(user)
        db.commit()
        db.refresh(user)

        return user


user_repository = UserRepository()
