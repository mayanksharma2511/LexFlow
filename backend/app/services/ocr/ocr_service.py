import fitz
import pytesseract

from PIL import Image


class OCRService:

    def extract_text(
        self,
        filepath: str,
    ) -> str:

        text = ""

        document = fitz.open(filepath)

        for page in document:

            page_text = page.get_text()

            if page_text.strip():
                text += page_text
                continue

            pix = page.get_pixmap()

            image = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples,
            )

            text += pytesseract.image_to_string(image)

        document.close()

        print("TYPE:", type(text), flush=True)
        print("HAS_NULL:", "\x00" in text, flush=True)
        print("TEXT PREVIEW:", repr(text[:300]), flush=True)
        
        return text


ocr_service = OCRService()