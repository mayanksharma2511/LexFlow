from app.services.ocr.ocr_service import ocr_service

print(
    ocr_service.extract_text(
        "uploads/documents/a7fd010c-b1bf-4dae-be62-c4d1b798a2f1.pdf"
    )
)