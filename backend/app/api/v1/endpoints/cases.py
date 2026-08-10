from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.dependencies.auth import get_current_user
from app.models.case_member import CaseMember
from app.models.user import User
from app.repositories.case_member import case_member_repository
from app.schemas.case import (
    CaseCreate,
    CaseDashboardResponse,
    CaseResponse,
    CaseStatsSummary,
    CaseUpdate,
)
from app.schemas.case_member import CaseMemberCreate, CaseMemberResponse
from app.services.case import case_service

router = APIRouter(
    prefix="/cases",
    tags=["Cases"],
)


@router.get(
    "/stats/summary",
    response_model=CaseStatsSummary,
)
def get_stats_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return case_service.get_stats_summary(db, current_user)


@router.post(
    "",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_case(
    case: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return case_service.create_case(
            db,
            case,
            current_user,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "",
    response_model=list[CaseResponse],
)
def get_my_cases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return case_service.get_my_cases(
        db,
        current_user,
    )

@router.get(
    "/{case_id}/dashboard",
    response_model=CaseDashboardResponse,
)
def get_case_dashboard(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    dashboard = case_service.get_dashboard(
        db=db,
        case_id=case_id,
        current_user=current_user,
    )

    if dashboard is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found.",
        )

    return dashboard

@router.get(
    "/{case_id}",
    response_model=CaseResponse,
)
def get_case(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = case_service.get_case(
        db,
        case_id,
        current_user,
    )

    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found.",
        )

    return case


@router.patch(
    "/{case_id}",
    response_model=CaseResponse,
)
def update_case(
    case_id: str,
    case_data: CaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = case_service.get_case(
        db,
        case_id,
        current_user,
    )

    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found.",
        )

    return case_service.update_case(
        db,
        case,
        case_data,
        current_user,
    )


@router.delete(
    "/{case_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_case(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = case_service.get_case(
        db,
        case_id,
        current_user,
    )

    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found.",
        )

    case_service.delete_case(
        db,
        case,
        current_user,
    )


@router.get(
    "/{case_id}/members",
    response_model=list[CaseMemberResponse],
)
def get_case_members(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = case_service.get_case(db, case_id, current_user)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")
    members = case_member_repository.get_by_case(db, case_id)
    results = []
    for m in members:
        user = db.query(User).filter(User.id == m.user_id).first()
        results.append(
            CaseMemberResponse(
                id=m.id,
                case_id=m.case_id,
                user_id=m.user_id,
                role_in_case=m.role_in_case,
                full_name=user.full_name if user else None,
                email=user.email if user else None,
                created_at=m.created_at,
            )
        )
    return results


@router.post(
    "/{case_id}/members",
    response_model=CaseMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_case_member(
    case_id: str,
    payload: CaseMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = case_service.get_case(db, case_id, current_user)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")

    existing = case_member_repository.get_by_case_and_user(db, case_id, payload.user_id)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member of this case.")

    member = CaseMember(
        case_id=case_id,
        user_id=payload.user_id,
        role_in_case=payload.role_in_case,
    )
    created = case_member_repository.create(db, member)
    user = db.query(User).filter(User.id == created.user_id).first()
    return CaseMemberResponse(
        id=created.id,
        case_id=created.case_id,
        user_id=created.user_id,
        role_in_case=created.role_in_case,
        full_name=user.full_name if user else None,
        email=user.email if user else None,
        created_at=created.created_at,
    )

