import logging
from pathlib import Path
from typing import Any

import fitz  # type: ignore[import-untyped]
import pytesseract  # type: ignore[import-untyped]
from PIL import Image

logger = logging.getLogger("lexflow.ocr")


class OCRService:

    def extract_text(
        self,
        filepath: str,
    ) -> str:
        """Extract text from PDF or image files using PyMuPDF and Tesseract OCR fallback."""
        file_path = Path(filepath)
        if not file_path.exists():
            logger.warning("File not found for OCR: %s", filepath)
            return ""

        extracted_parts: list[str] = []

        try:
            with fitz.open(str(file_path)) as document:
                for page in document:
                    raw_text: Any = page.get_text("text")
                    page_text: str = raw_text if isinstance(raw_text, str) else ""

                    # If page contains selectable text, use it directly
                    if page_text.strip():
                        extracted_parts.append(page_text)
                        continue

                    # Fallback to OCR for scanned/image pages
                    try:
                        pix: Any = page.get_pixmap()
                        image = Image.frombytes(
                            "RGB",
                            (pix.width, pix.height),
                            pix.samples,
                        )
                        raw_ocr: Any = pytesseract.image_to_string(image)
                        ocr_text: str = (
                            raw_ocr.decode("utf-8", errors="ignore")
                            if isinstance(raw_ocr, bytes)
                            else str(raw_ocr or "")
                        )

                        if ocr_text.strip():
                            extracted_parts.append(ocr_text)
                    except Exception as ocr_err:  # noqa: BLE001
                        logger.warning("OCR page extraction warning for %s: %s", filepath, ocr_err)

        except Exception as err:  # noqa: BLE001
            logger.error("Failed to open document %s: %s", filepath, err)

        full_text = "\n".join(extracted_parts)
        # Sanitize text by stripping NUL bytes for PostgreSQL compatibility
        return full_text.replace("\x00", "").strip()


ocr_service = OCRService()
