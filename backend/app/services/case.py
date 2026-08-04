from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.user import User
from app.repositories.case import case_repository
from app.schemas.case import CaseCreate, CaseUpdate


class CaseService:

    def create_case(
        self,
        db: Session,
        case_data: CaseCreate,
        current_user: User,
    ) -> Case:

        case = Case(
            title=case_data.title,
            case_number=case_data.case_number,
            client_name=case_data.client_name,
            opposing_party=case_data.opposing_party,
            court=case_data.court,
            description=case_data.description,
            owner_id=current_user.id,
        )

        return case_repository.create(db, case)

    def get_my_cases(
        self,
        db: Session,
        current_user: User,
    ) -> list[Case]:

        return case_repository.get_all_by_owner(
            db,
            current_user.id,
        )

    def get_case(
        self,
        db: Session,
        case_id: str,
        current_user: User,
    ) -> Case | None:

        case = case_repository.get_by_id(db, case_id)

        if case is None:
            return None

        if case.owner_id != current_user.id:
            return None

        return case

    def update_case(
        self,
        db: Session,
        case: Case,
        case_data: CaseUpdate,
    ) -> Case:

        updates = case_data.model_dump(exclude_unset=True)

        for field, value in updates.items():
            setattr(case, field, value)

        return case_repository.update(db, case)

    def delete_case(
        self,
        db: Session,
        case: Case,
    ) -> None:

        case_repository.delete(db, case)


case_service = CaseService()