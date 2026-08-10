from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.document import Document


class DocumentRepository:

    def create(
        self,
        db: Session,
        document: Document,
    ) -> Document:

        db.add(document)
        db.commit()
        db.refresh(document)

        return document

    def get_by_case(
        self,
        db: Session,
        case_id: str,
        user_id: str | None = None,
    ) -> list[Document]:
        query = db.query(Document).filter(Document.case_id == case_id)
        if user_id:
            query = query.join(Case, Document.case_id == Case.id).filter(Case.owner_id == user_id)
        return query.all()

    def get_by_id(
        self,
        db: Session,
        document_id: str,
    ) -> Document | None:

        return (
            db.query(Document)
            .filter(Document.id == document_id)
            .first()
        )

    def get_by_id_for_user(
        self,
        db: Session,
        document_id: str,
        user_id: str,
    ) -> Document | None:

        return (
            db.query(Document)
            .join(Case, Document.case_id == Case.id)
            .filter(
                Document.id == document_id,
                Case.owner_id == user_id,
            )
            .first()
        )

    def get_all(
        self,
        db: Session,
    ) -> list[Document]:

        return (
            db.query(Document)
            .all()
        )

    def get_all_by_user(
        self,
        db: Session,
        user_id: str,
    ) -> list[Document]:

        return (
            db.query(Document)
            .join(Case, Document.case_id == Case.id)
            .filter(Case.owner_id == user_id)
            .all()
        )

    def update(
        self,
        db: Session,
        document: Document,
    ) -> Document:

        db.commit()
        db.refresh(document)

        return document

    def delete(
        self,
        db: Session,
        document: Document,
    ) -> None:

        db.delete(document)
        db.commit()


document_repository = DocumentRepository()
