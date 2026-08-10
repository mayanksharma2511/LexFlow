from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.ai import (
    AnalysisHistoryResponse,
    ClassificationResponse,
    ClauseExtractionResponse,
    ComparisonResponse,
    LatestAnalysisResponse,
    RiskAnalysisResponse,
    SummaryResponse,
)
from app.services.ai.analysis_service import ai_analysis_service

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


@router.post(
    "/documents/{document_id}/summary",
    response_model=SummaryResponse,
)
def summarize_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    try:
        summary = ai_analysis_service.summarize(
            db=db,
            document_id=document_id,
            user_id=current_user.id,
        )

        return SummaryResponse(
            summary=summary,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/documents/{document_id}/extract-clauses",
    response_model=ClauseExtractionResponse,
)
def extract_clauses(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    try:
        result = ai_analysis_service.extract_clauses(
            db=db,
            document_id=document_id,
            user_id=current_user.id,
        )

        return ClauseExtractionResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/documents/{document_id}/classify",
    response_model=ClassificationResponse,
)
def classify_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    try:
        result = ai_analysis_service.classify(
            db=db,
            document_id=document_id,
            user_id=current_user.id,
        )

        return ClassificationResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/documents/{document_id}/risk-analysis",
    response_model=RiskAnalysisResponse,
)
def analyze_risks(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    try:
        result = ai_analysis_service.analyze_risks(
            db=db,
            document_id=document_id,
            user_id=current_user.id,
        )

        return RiskAnalysisResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/documents/{old_document_id}/compare/{new_document_id}",
    response_model=ComparisonResponse,
)
def compare_documents(
    old_document_id: str,
    new_document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    try:
        result = ai_analysis_service.compare_documents(
            db=db,
            old_document_id=old_document_id,
            new_document_id=new_document_id,
            user_id=current_user.id,
        )

        return ComparisonResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/documents/{document_id}/analyses",
    response_model=list[AnalysisHistoryResponse],
)
def get_document_analyses(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    try:
        return ai_analysis_service.get_document_analyses(
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
    "/documents/{document_id}/analyses/{analysis_type}",
    response_model=LatestAnalysisResponse,
)
def get_latest_analysis(
    document_id: str,
    analysis_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    try:
        analysis = ai_analysis_service.get_latest_analysis(
            db=db,
            document_id=document_id,
            analysis_type=analysis_type,
            user_id=current_user.id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found.",
        )

    return analysis


@router.post("/cases/{case_id}/synthesis")
def synthesize_case_analysis(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return ai_analysis_service.synthesize_case_analysis(
            db=db,
            case_id=case_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
