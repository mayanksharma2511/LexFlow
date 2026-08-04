from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.case import CaseCreate, CaseResponse, CaseUpdate
from app.services.case import case_service

router = APIRouter(
    prefix="/cases",
    tags=["Cases"],
)


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
    return case_service.create_case(
        db,
        case,
        current_user,
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
    )