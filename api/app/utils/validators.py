import base64
import io
from PIL import Image
from fastapi import UploadFile

from ..config import get_settings
from .exceptions import ImageValidationError


def validate_image_count(images: list) -> None:
    """Validate the number of images is within allowed range (1-5)."""
    settings = get_settings()

    if len(images) < settings.min_images:
        raise ImageValidationError(
            message="No images provided",
            detail=f"At least {settings.min_images} image(s) required",
        )

    if len(images) > settings.max_images:
        raise ImageValidationError(
            message="Too many images",
            detail=f"Maximum {settings.max_images} images allowed",
        )


def decode_base64_image(base64_string: str, index: int = 0) -> tuple[bytes, Image.Image]:
    """Decode base64 string to image bytes and PIL Image."""
    try:
        # Handle data URL format (data:image/jpeg;base64,...)
        if "," in base64_string:
            base64_string = base64_string.split(",", 1)[1]

        image_data = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_data))
        return image_data, image
    except Exception as e:
        raise ImageValidationError(
            message="Invalid base64 image",
            detail=f"Failed to decode image at index {index}: {str(e)}",
        )


async def read_upload_file(file: UploadFile) -> tuple[bytes, Image.Image]:
    """Read an uploaded file."""
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        return contents, image
    except Exception as e:
        raise ImageValidationError(
            message="Invalid image file",
            detail=f"Failed to read image '{file.filename}': {str(e)}",
        )
