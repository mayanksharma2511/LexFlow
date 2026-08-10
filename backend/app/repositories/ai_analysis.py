from sqlalchemy.orm import Session

from app.models.ai_analysis import AIAnalysis


class AIAnalysisRepository:

    def create(
        self,
        db: Session,
        analysis: AIAnalysis,
    ) -> AIAnalysis:

        db.add(analysis)
        db.commit()
        db.refresh(analysis)

        return analysis

    def get_by_document_and_type(
        self,
        db: Session,
        document_id: str,
        analysis_type: str,
    ) -> AIAnalysis | None:

        return (
            db.query(AIAnalysis)
            .filter(
                AIAnalysis.document_id == document_id,
                AIAnalysis.analysis_type == analysis_type,
            )
            .order_by(AIAnalysis.created_at.desc())
            .first()
        )

    def get_all_by_document(
        self,
        db: Session,
        document_id: str,
    ) -> list[AIAnalysis]:

        return (
            db.query(AIAnalysis)
            .filter(
                AIAnalysis.document_id == document_id,
            )
            .order_by(AIAnalysis.created_at.desc())
            .all()
        )

    def get_count_by_document(
        self,
        db: Session,
        document_id: str,
    ) -> int:

        return (
            db.query(AIAnalysis)
            .filter(
                AIAnalysis.document_id == document_id,
            )
            .count()
        )


ai_analysis_repository = AIAnalysisRepository()
