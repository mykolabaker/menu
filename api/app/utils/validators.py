import base64
import io
from PIL import Image
from fastapi import UploadFile

from ..config import get_settings
from .exceptions import ImageValidationError


def validate_image_count(images: list) -> None:
    """Validate the number of images is within allowed range."""
    settings = get_settings()

    if len(images) < settings.min_images:
        raise ImageValidationError(
            message="Too few images",
            detail=f"At least {settings.min_images} image(s) required, got {len(images)}",
        )

    if len(images) > settings.max_images:
        raise ImageValidationError(
            message="Too many images",
            detail=f"Maximum {settings.max_images} images allowed, got {len(images)}",
        )


def validate_image_format(image: Image.Image, filename: str = "image") -> None:
    """Validate image format is allowed."""
    settings = get_settings()

    if image.format:
        fmt = image.format.lower()
    else:
        fmt = "unknown"

    if fmt not in settings.allowed_image_formats:
        raise ImageValidationError(
            message="Invalid image format",
            detail=f"Image '{filename}' has format '{fmt}'. Allowed: {settings.allowed_image_formats}",
        )


def validate_image_size(data: bytes, filename: str = "image") -> None:
    """Validate image size is within limit."""
    settings = get_settings()
    max_bytes = settings.max_image_size_mb * 1024 * 1024

    if len(data) > max_bytes:
        size_mb = len(data) / (1024 * 1024)
        raise ImageValidationError(
            message="Image too large",
            detail=f"Image '{filename}' is {size_mb:.2f}MB. Maximum allowed: {settings.max_image_size_mb}MB",
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
    """Read and validate an uploaded file."""
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        return contents, image
    except Exception as e:
        raise ImageValidationError(
            message="Invalid image file",
            detail=f"Failed to read image '{file.filename}': {str(e)}",
        )


def validate_image(
    image_data: bytes, image: Image.Image, filename: str = "image"
) -> None:
    """Run all validations on a single image."""
    validate_image_size(image_data, filename)
    validate_image_format(image, filename)

    # Verify image can be processed
    try:
        image.verify()
        # Re-open after verify (verify closes the file)
        image = Image.open(io.BytesIO(image_data))
        image.load()
    except Exception as e:
        raise ImageValidationError(
            message="Corrupted image",
            detail=f"Image '{filename}' appears to be corrupted: {str(e)}",
        )
