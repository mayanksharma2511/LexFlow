from sqlalchemy.orm import Session

from app.models.case import Case


class CaseRepository:

    def create(
        self,
        db: Session,
        case: Case,
    ) -> Case:

        db.add(case)
        db.commit()
        db.refresh(case)

        return case

    def get_all_by_owner(
        self,
        db: Session,
        owner_id: str,
    ) -> list[Case]:

        return (
            db.query(Case)
            .filter(Case.owner_id == owner_id)
            .all()
        )

    def get_by_id(
        self,
        db: Session,
        case_id: str,
    ) -> Case | None:

        return (
            db.query(Case)
            .filter(Case.id == case_id)
            .first()
        )

    def update(
        self,
        db: Session,
        case: Case,
    ) -> Case:

        db.commit()
        db.refresh(case)

        return case

    def delete(
        self,
        db: Session,
        case: Case,
    ) -> None:

        db.delete(case)
        db.commit()


case_repository = CaseRepository()