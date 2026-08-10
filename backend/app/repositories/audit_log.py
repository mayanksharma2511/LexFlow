from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditLogRepository:

    def create(
        self,
        db: Session,
        audit_log: AuditLog,
    ) -> AuditLog:

        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)

        return audit_log

    def get_by_user(
        self,
        db: Session,
        user_id: str,
    ) -> list[AuditLog]:

        return (
            db.query(AuditLog)
            .filter(
                AuditLog.user_id == user_id,
            )
            .order_by(
                AuditLog.created_at.desc()
            )
            .all()
        )

    def get_by_entity(
        self,
        db: Session,
        entity_type: str,
        entity_id: str,
    ) -> list[AuditLog]:

        return (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id,
            )
            .order_by(
                AuditLog.created_at.desc()
            )
            .all()
        )


audit_log_repository = AuditLogRepository()
