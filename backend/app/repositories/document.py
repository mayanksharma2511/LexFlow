from sqlalchemy.orm import Session

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
    ) -> list[Document]:

        return (
            db.query(Document)
            .filter(Document.case_id == case_id)
            .all()
        )

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

    def update(
        self,
        db: Session,
        document: Document,
    ) -> Document:

        db.commit()
        db.refresh(document)

        return document

    def get_all(
        self,
        db: Session,
    ) -> list[Document]:

        return db.query(Document).all()

    def delete(
        self,
        db: Session,
        document: Document,
    ) -> None:

        db.delete(document)
        db.commit()


document_repository = DocumentRepository()