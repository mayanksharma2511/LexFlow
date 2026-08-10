from sqlalchemy.orm import Session

from app.enums.case_priority import CasePriority
from app.models.case import Case
from app.models.user import User
from app.repositories.ai_analysis import ai_analysis_repository
from app.repositories.case import case_repository
from app.repositories.document import document_repository
from app.schemas.case import CaseCreate, CaseUpdate
from app.services.audit_log import audit_log_service


class CaseService:

    def create_case(
        self,
        db: Session,
        case_data: CaseCreate,
        current_user: User,
    ) -> Case:
        p_str = str(case_data.priority or "MEDIUM").upper()
        if "LOW" in p_str:
            priority_val = CasePriority.LOW
        elif "HIGH" in p_str or "URGENT" in p_str:
            priority_val = CasePriority.HIGH
        else:
            priority_val = CasePriority.MEDIUM

        case = Case(
            title=case_data.title,
            case_number=case_data.case_number,
            client_name=case_data.client_name,
            opposing_party=case_data.opposing_party,
            court=case_data.court,
            description=case_data.description,
            priority=priority_val,
            owner_id=current_user.id,
        )

        try:
            case = case_repository.create(
                db,
                case,
            )
        except Exception as err:
            db.rollback()
            if "case_number" in str(err).lower() or "unique" in str(err).lower():
                raise ValueError(f"Case Number '{case_data.case_number}' already exists. Please use a unique case number.") from err
            raise

        audit_log_service.log(
            db=db,
            user_id=current_user.id,
            action="CASE_CREATE",
            entity_type="case",
            entity_id=case.id,
            details=f"Case '{case.title}' was created.",
        )

        return case

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

        case = case_repository.get_by_id(
            db,
            case_id,
        )

        if case is None:
            return None

        if case.owner_id != current_user.id:
            return None

        return case

    def get_dashboard(
        self,
        db: Session,
        case_id: str,
        current_user: User,
    ):

        case = case_repository.get_by_id(
            db,
            case_id,
        )

        if case is None:
            raise ValueError("Case not found.")

        if case.owner_id != current_user.id:
            raise ValueError("Case not found.")

        documents = document_repository.get_by_case(
            db,
            case_id,
            current_user.id,
        )

        dashboard_documents = []

        for document in documents:

            analysis_count = (
                ai_analysis_repository.get_count_by_document(
                    db,
                    document.id,
                )
            )

            dashboard_documents.append(
                {
                    "id": document.id,
                    "file_name": document.file_name,
                    "document_type": document.document_type,
                    "uploaded_at": document.uploaded_at,
                    "analysis_count": analysis_count,
                }
            )

        return {
            "id": case.id,
            "title": case.title,
            "case_number": case.case_number,
            "client_name": case.client_name,
            "opposing_party": case.opposing_party,
            "court": case.court,
            "description": case.description,
            "status": case.status,
            "priority": case.priority,
            "documents": dashboard_documents,
            "document_count": len(documents),
        }

    def update_case(
        self,
        db: Session,
        case: Case,
        case_data: CaseUpdate,
        current_user: User,
    ) -> Case:

        updates = case_data.model_dump(
            exclude_unset=True,
        )

        for field, value in updates.items():
            setattr(case, field, value)

        case = case_repository.update(
            db,
            case,
        )

        audit_log_service.log(
            db=db,
            user_id=current_user.id,
            action="CASE_UPDATE",
            entity_type="case",
            entity_id=case.id,
            details=f"Case '{case.title}' was updated.",
        )

        return case

    def delete_case(
        self,
        db: Session,
        case: Case,
        current_user: User,
    ) -> None:

        case_id = case.id
        case_title = case.title

        case_repository.delete(
            db,
            case,
        )

        audit_log_service.log(
            db=db,
            user_id=current_user.id,
            action="CASE_DELETE",
            entity_type="case",
            entity_id=case_id,
            details=f"Case '{case_title}' was deleted.",
        )

    def get_stats_summary(
        self,
        db: Session,
        current_user: User,
    ) -> dict[str, int]:
        cases = case_repository.get_all_by_owner(db, current_user.id)
        active_cases = len([c for c in cases if c.status.lower() != "closed"])

        documents = document_repository.get_all_by_user(db, current_user.id)
        total_documents = len(documents)

        total_ai_analyses = sum(
            ai_analysis_repository.get_count_by_document(db, doc.id)
            for doc in documents
        )

        pending_review = len([c for c in cases if c.status.lower() == "review" or c.priority.lower() == "high"])

        return {
            "active_cases": active_cases,
            "total_documents": total_documents,
            "total_ai_analyses": total_ai_analyses,
            "pending_review": pending_review,
        }


case_service = CaseService()
