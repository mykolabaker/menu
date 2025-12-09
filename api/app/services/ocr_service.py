import time
import pytesseract
from PIL import Image
import structlog

from .image_preprocessor import image_preprocessor
from ..utils.exceptions import OCRError

logger = structlog.get_logger()


class OCRService:
    """Service for extracting text from images using Tesseract OCR."""

    def __init__(self):
        # Tesseract configuration for menu text
        self.config = "--oem 3 --psm 6"  # LSTM OCR, assume uniform block of text

    def extract_text(self, image: Image.Image, request_id: str = "", image_index: int = 0) -> str:
        """
        Extract text from a single image.

        Args:
            image: PIL Image to process
            request_id: Request ID for logging
            image_index: Index of image in batch

        Returns:
            Extracted text from the image
        """
        log = logger.bind(request_id=request_id, image_index=image_index)
        log.info("ocr_started")

        start_time = time.time()

        try:
            # Preprocess image
            preprocessed = image_preprocessor.preprocess(image, request_id)

            # Run OCR
            text = pytesseract.image_to_string(preprocessed, config=self.config)

            duration_ms = int((time.time() - start_time) * 1000)
            log.info(
                "ocr_completed",
                extracted_text_length=len(text),
                duration_ms=duration_ms,
            )

            return text.strip()

        except Exception as e:
            log.error("ocr_failed", error=str(e))
            raise OCRError(
                message="OCR processing failed",
                detail=f"Failed to extract text from image {image_index}: {str(e)}",
            )

    def extract_text_batch(
        self, images: list[Image.Image], request_id: str = ""
    ) -> list[str]:
        """
        Extract text from multiple images.

        Args:
            images: List of PIL Images
            request_id: Request ID for logging

        Returns:
            List of extracted text strings
        """
        results = []
        for i, image in enumerate(images):
            text = self.extract_text(image, request_id, i)
            results.append(text)
        return results


# Singleton instance
ocr_service = OCRService()
