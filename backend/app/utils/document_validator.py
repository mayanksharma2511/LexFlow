from fastapi import HTTPException, UploadFile, status

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".png",
    ".jpg",
    ".jpeg",
}

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


def validate_file(file: UploadFile) -> None:

    extension = "." + file.filename.split(".")[-1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type.",
        )


def validate_file_size(file: UploadFile) -> None:

    file.file.seek(0, 2)

    size = file.file.tell()

    file.file.seek(0)

    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File exceeds 20 MB limit.",
        )