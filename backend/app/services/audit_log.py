from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.repositories.audit_log import audit_log_repository


class AuditLogService:

    def log(
        self,
        db: Session,
        user_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        details: str | None = None,
    ) -> AuditLog:

        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )

        return audit_log_repository.create(
            db,
            audit_log,
        )

    def get_user_logs(
        self,
        db: Session,
        user_id: str,
    ) -> list[AuditLog]:

        return audit_log_repository.get_by_user(
            db,
            user_id,
        )

    def get_entity_logs(
        self,
        db: Session,
        entity_type: str,
        entity_id: str,
    ) -> list[AuditLog]:

        return audit_log_repository.get_by_entity(
            db,
            entity_type,
            entity_id,
        )

    def get_document_logs(
        self,
        db: Session,
        document_id: str,
        user_id: str,
    ) -> list[AuditLog]:

        return audit_log_repository.get_by_entity(
            db,
            "document",
            document_id,
        )

    def get_case_logs(
        self,
        db: Session,
        case_id: str,
        user_id: str,
    ) -> list[AuditLog]:

        return audit_log_repository.get_by_entity(
            db,
            "case",
            case_id,
        )


audit_log_service = AuditLogService()
