import io
import cv2
import numpy as np
from PIL import Image
import structlog

logger = structlog.get_logger()


class ImagePreprocessor:
    """Preprocesses images to improve OCR accuracy."""

    def preprocess(self, image: Image.Image, request_id: str = "") -> Image.Image:
        """
        Apply preprocessing pipeline to improve OCR quality.

        Steps:
        1. Convert to grayscale
        2. Apply noise reduction
        3. Enhance contrast
        4. Deskew if needed
        """
        log = logger.bind(request_id=request_id)
        log.debug("Starting image preprocessing")

        # Convert PIL to OpenCV format
        cv_image = self._pil_to_cv(image)

        # Apply preprocessing steps
        cv_image = self._to_grayscale(cv_image)
        cv_image = self._reduce_noise(cv_image)
        cv_image = self._enhance_contrast(cv_image)
        cv_image = self._deskew(cv_image)

        # Convert back to PIL
        result = self._cv_to_pil(cv_image)
        log.debug("Image preprocessing completed")

        return result

    def _pil_to_cv(self, pil_image: Image.Image) -> np.ndarray:
        """Convert PIL Image to OpenCV format."""
        # Convert to RGB if necessary
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    def _cv_to_pil(self, cv_image: np.ndarray) -> Image.Image:
        """Convert OpenCV image to PIL format."""
        if len(cv_image.shape) == 2:
            # Grayscale
            return Image.fromarray(cv_image)
        else:
            # BGR to RGB
            return Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))

    def _to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """Convert image to grayscale."""
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image

    def _reduce_noise(self, image: np.ndarray) -> np.ndarray:
        """Apply noise reduction using fastNlMeansDenoising."""
        return cv2.fastNlMeansDenoising(image, None, h=10, templateWindowSize=7, searchWindowSize=21)

    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Enhance contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)."""
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(image)

    def _deskew(self, image: np.ndarray) -> np.ndarray:
        """Deskew image using Hough transform to detect lines."""
        # Find edges
        edges = cv2.Canny(image, 50, 150, apertureSize=3)

        # Detect lines using Hough transform
        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180, threshold=100, minLineLength=100, maxLineGap=10
        )

        if lines is None or len(lines) == 0:
            return image

        # Calculate angles of lines
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 - x1 != 0:
                angle = np.arctan((y2 - y1) / (x2 - x1)) * 180 / np.pi
                # Only consider near-horizontal lines
                if abs(angle) < 30:
                    angles.append(angle)

        if not angles:
            return image

        # Use median angle to avoid outliers
        median_angle = np.median(angles)

        # Only deskew if angle is significant
        if abs(median_angle) < 0.5:
            return image

        # Rotate image
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        rotated = cv2.warpAffine(
            image,
            rotation_matrix,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )

        return rotated


# Singleton instance
image_preprocessor = ImagePreprocessor()
