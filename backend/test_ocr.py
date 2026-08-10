from pathlib import Path

from app.services.ocr.ocr_service import ocr_service

if __name__ == "__main__":
    sample_file = Path("uploads/documents/a7fd010c-b1bf-4dae-be62-c4d1b798a2f1.pdf")
    if sample_file.exists():
        print(ocr_service.extract_text(str(sample_file)))
    else:
        print(f"Sample file not found at {sample_file}")
