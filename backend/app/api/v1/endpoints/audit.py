from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.audit_log import AuditLogResponse
from app.services.audit_log import audit_log_service

router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
)


@router.get(
    "",
    response_model=list[AuditLogResponse],
)
def get_my_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return audit_log_service.get_user_logs(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/documents/{document_id}",
    response_model=list[AuditLogResponse],
)
def get_document_audit_logs(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    try:
        return audit_log_service.get_document_logs(
            db=db,
            document_id=document_id,
            user_id=current_user.id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/cases/{case_id}",
    response_model=list[AuditLogResponse],
)
def get_case_audit_logs(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return audit_log_service.get_case_logs(
            db=db,
            case_id=case_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
