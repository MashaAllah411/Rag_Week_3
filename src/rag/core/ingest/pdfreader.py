import os
import io
import shutil
import logging
from typing import List, Optional
from pypdf import PdfReader

logger = logging.getLogger(__name__)

# ── Optional OCR imports & initialization ────────────────────
OCR_AVAILABLE = False
_TESSERACT_CMD = None

try:
    import pytesseract
    from PIL import Image

    # Auto-detect Tesseract binary path on Windows and Linux/macOS
    _CANDIDATE_PATHS = [
        os.environ.get("TESSERACT_PATH", ""),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        shutil.which("tesseract") or "",
    ]
    for _path in _CANDIDATE_PATHS:
        if _path and os.path.isfile(_path):
            pytesseract.pytesseract.tesseract_cmd = _path
            _TESSERACT_CMD = _path
            break

    # Verify Tesseract is executable
    try:
        _ver = pytesseract.get_tesseract_version()
        OCR_AVAILABLE = True
        logger.info(f"Tesseract OCR enabled (version: {_ver}, path: {_TESSERACT_CMD or 'default PATH'})")
    except Exception as _e:
        logger.warning(f"pytesseract installed but Tesseract executable failed: {_e}. OCR disabled.")
        OCR_AVAILABLE = False

except ImportError:
    OCR_AVAILABLE = False
    logger.warning("pytesseract or Pillow not installed — OCR disabled.")


def is_ocr_available() -> bool:
    """Check if OCR is configured and operational."""
    return OCR_AVAILABLE


def _ocr_images_from_page(page, min_width: int = 40, min_height: int = 40) -> str:
    """
    Extract text from embedded images in a single PDF page using pytesseract OCR.
    Handles image mode conversions and skips non-text decorative icons.
    """
    if not OCR_AVAILABLE:
        return ""

    ocr_texts = []
    try:
        images = list(page.images)
    except Exception as page_err:
        logger.debug(f"Could not iterate page images: {page_err}")
        return ""

    for img_obj in images:
        try:
            image = Image.open(io.BytesIO(img_obj.data))

            # Skip tiny icons or spacer lines
            if image.width < min_width or image.height < min_height:
                continue

            # Handle RGBA/transparency by pasting on a clean white background
            if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
                bg = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode != "RGBA":
                    image = image.convert("RGBA")
                bg.paste(image, mask=image.split()[3])
                image = bg
            elif image.mode not in ("L", "RGB"):
                image = image.convert("RGB")

            text = pytesseract.image_to_string(image).strip()
            if text:
                ocr_texts.append(text)
        except Exception as img_err:
            logger.debug(f"Skipping image OCR: {img_err}")

    return "\n".join(ocr_texts)


def read_pdf(
    pdf_path: str,
    extract_mode: str = "hybrid",
    min_image_size: tuple = (40, 40)
) -> List[str]:
    """
    Extract text from a PDF file with optional OCR support.

    Parameters:
        pdf_path (str): Path to the PDF file.
        extract_mode (str):
            - "hybrid": Standard text extraction + OCR on embedded images (default).
            - "fallback": Use standard text; run OCR only if page text is minimal (<50 chars).
            - "ocr_only": Use only OCR on embedded images.
            - "text_only": Standard pypdf text extraction (no OCR).
        min_image_size (tuple): (min_width, min_height) to ignore tiny decorative icons during OCR.

    Returns:
        List[str]: Extracted text content for each page in the PDF.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"The file {pdf_path} does not exist.")

    reader = PdfReader(pdf_path)
    pages = []
    min_w, min_h = min_image_size

    for page in reader.pages:
        text = ""

        if extract_mode in ("hybrid", "text_only", "fallback"):
            text = (page.extract_text() or "").strip()

        if extract_mode == "hybrid" and OCR_AVAILABLE:
            ocr_text = _ocr_images_from_page(page, min_width=min_w, min_height=min_h)
            if ocr_text:
                text = f"{text}\n\n[OCR]\n{ocr_text}" if text else f"[OCR]\n{ocr_text}"

        elif extract_mode == "fallback" and OCR_AVAILABLE:
            # If extracted text is empty or very short, attempt OCR
            if len(text) < 50:
                ocr_text = _ocr_images_from_page(page, min_width=min_w, min_height=min_h)
                if ocr_text:
                    text = f"{text}\n\n[OCR]\n{ocr_text}" if text else f"[OCR]\n{ocr_text}"

        elif extract_mode == "ocr_only" and OCR_AVAILABLE:
            text = _ocr_images_from_page(page, min_width=min_w, min_height=min_h)

        pages.append(text)

    status_msg = f"PDF read complete — {len(pages)} pages (mode='{extract_mode}', OCR={'active' if OCR_AVAILABLE else 'disabled'})"
    logger.info(status_msg)

    return pages

