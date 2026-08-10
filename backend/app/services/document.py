import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.document import Document
from app.repositories.document import document_repository
from app.schemas.document import DocumentCreate
from app.services.audit_log import audit_log_service
from app.services.ocr.ocr_service import ocr_service
from app.utils.document_validator import (
    validate_file,
    validate_file_size,
)
from app.utils.file import UPLOAD_FOLDER


class DocumentService:

    def upload_document(
        self,
        db: Session,
        file: UploadFile,
        data: DocumentCreate,
        user_id: str,
    ) -> Document:

        case = (
            db.query(Case)
            .filter(
                Case.id == data.case_id,
                Case.owner_id == user_id,
            )
            .first()
        )

        if case is None:
            raise ValueError("Case not found.")

        validate_file(file)
        validate_file_size(file)

        extension = Path(file.filename or "").suffix
        filename = f"{uuid.uuid4()}{extension}"

        filepath = UPLOAD_FOLDER / filename

        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(
                file.file,
                buffer,
            )

        text = ocr_service.extract_text(
            str(filepath),
        )

        document = Document(
            file_name=file.filename,
            file_path=str(filepath),
            extracted_text=text,
            document_type=data.document_type,
            case_id=data.case_id,
        )

        document = document_repository.create(
            db,
            document,
        )

        audit_log_service.log(
            db=db,
            user_id=user_id,
            action="DOCUMENT_UPLOAD",
            entity_type="document",
            entity_id=document.id,
            details=f"Document '{document.file_name}' was uploaded.",
        )

        return document

    def get_user_documents(
        self,
        db: Session,
        user_id: str,
    ) -> list[Document]:

        return (
            db.query(Document)
            .join(Case, Document.case_id == Case.id)
            .filter(
                Case.owner_id == user_id,
            )
            .all()
        )

    def get_user_document(
        self,
        db: Session,
        document_id: str,
        user_id: str,
    ) -> Document | None:

        return document_repository.get_by_id_for_user(
            db,
            document_id,
            user_id,
        )

    def get_all_documents(
        self,
        db: Session,
    ) -> list[Document]:

        return document_repository.get_all(
            db,
        )

    def get_case_documents(
        self,
        db: Session,
        case_id: str,
        user_id: str,
    ) -> list[Document]:

        return document_repository.get_by_case(
            db,
            case_id,
            user_id,
        )

    def get_document(
        self,
        db: Session,
        document_id: str,
    ) -> Document | None:

        return document_repository.get_by_id(
            db,
            document_id,
        )

    def delete_document(
        self,
        db: Session,
        document_id: str,
        user_id: str,
    ) -> None:

        document = document_repository.get_by_id_for_user(
            db,
            document_id,
            user_id,
        )

        if document is None:
            raise ValueError("Document not found.")

        document_id = document.id
        file_name = document.file_name

        filepath = Path(
            document.file_path,
        )

        if filepath.exists():
            filepath.unlink()

        document_repository.delete(
            db,
            document,
        )

        audit_log_service.log(
            db=db,
            user_id=user_id,
            action="DOCUMENT_DELETE",
            entity_type="document",
            entity_id=document_id,
            details=f"Document '{file_name}' was deleted.",
        )


document_service = DocumentService()
