from pathlib import Path
import shutil
import uuid

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.document import Document
from app.repositories.document import document_repository
from app.schemas.document import DocumentCreate
from app.utils.file import UPLOAD_FOLDER


class DocumentService:

    def upload_document(
        self,
        db: Session,
        file: UploadFile,
        data: DocumentCreate,
    ) -> Document:

        extension = Path(file.filename).suffix

        filename = f"{uuid.uuid4()}{extension}"

        filepath = UPLOAD_FOLDER / filename

        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        document = Document(
            file_name=file.filename,
            file_path=str(filepath),
            document_type=data.document_type,
            case_id=data.case_id,
        )

        return document_repository.create(
            db,
            document,
        )

    def get_all_documents(
        self,
        db: Session,
    ) -> list[Document]:

        return document_repository.get_all(db)

    def get_case_documents(
        self,
        db: Session,
        case_id: str,
    ) -> list[Document]:

        return document_repository.get_by_case(
            db,
            case_id,
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


document_service = DocumentService()