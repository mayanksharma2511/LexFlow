from pathlib import Path

UPLOAD_FOLDER = Path("uploads/documents")

UPLOAD_FOLDER.mkdir(
    parents=True,
    exist_ok=True,
)