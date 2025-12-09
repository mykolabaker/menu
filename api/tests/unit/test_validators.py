import pytest
import io
import base64
from PIL import Image
from unittest.mock import patch

from app.utils.validators import (
    validate_image_count,
    validate_image_format,
    validate_image_size,
    decode_base64_image,
    validate_image,
)
from app.utils.exceptions import ImageValidationError


class TestValidateImageCount:
    def test_valid_single_image(self):
        """Test validation passes with single image."""
        validate_image_count(["image1"])  # Should not raise

    def test_valid_five_images(self):
        """Test validation passes with max images."""
        validate_image_count(["img1", "img2", "img3", "img4", "img5"])

    def test_too_few_images(self):
        """Test validation fails with no images."""
        with pytest.raises(ImageValidationError) as exc_info:
            validate_image_count([])
        assert "Too few images" in exc_info.value.message

    def test_too_many_images(self):
        """Test validation fails with too many images."""
        with pytest.raises(ImageValidationError) as exc_info:
            validate_image_count(["img"] * 6)
        assert "Too many images" in exc_info.value.message


class TestValidateImageFormat:
    def test_valid_jpeg_format(self, sample_image_bytes):
        """Test JPEG format is accepted."""
        img = Image.open(io.BytesIO(sample_image_bytes))
        validate_image_format(img, "test.jpg")  # Should not raise

    def test_valid_png_format(self):
        """Test PNG format is accepted."""
        img = Image.new("RGB", (100, 100))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        img = Image.open(buffer)
        validate_image_format(img, "test.png")  # Should not raise


class TestValidateImageSize:
    def test_valid_size(self, sample_image_bytes):
        """Test valid image size passes."""
        validate_image_size(sample_image_bytes, "test.jpg")  # Should not raise

    def test_too_large(self):
        """Test oversized image fails."""
        # Create data larger than 10MB
        large_data = b"x" * (11 * 1024 * 1024)
        with pytest.raises(ImageValidationError) as exc_info:
            validate_image_size(large_data, "large.jpg")
        assert "too large" in exc_info.value.message.lower()


class TestDecodeBase64Image:
    def test_valid_base64(self, sample_image_bytes):
        """Test valid base64 decoding."""
        b64_string = base64.b64encode(sample_image_bytes).decode()
        data, img = decode_base64_image(b64_string, 0)
        assert len(data) > 0
        assert img is not None

    def test_data_url_format(self, sample_image_bytes):
        """Test data URL format with prefix."""
        b64_string = base64.b64encode(sample_image_bytes).decode()
        data_url = f"data:image/jpeg;base64,{b64_string}"
        data, img = decode_base64_image(data_url, 0)
        assert len(data) > 0
        assert img is not None

    def test_invalid_base64(self):
        """Test invalid base64 raises error."""
        with pytest.raises(ImageValidationError) as exc_info:
            decode_base64_image("not-valid-base64!!!", 0)
        assert "Invalid base64" in exc_info.value.message


class TestValidateImage:
    def test_valid_image(self, sample_image_bytes):
        """Test full validation of valid image."""
        img = Image.open(io.BytesIO(sample_image_bytes))
        validate_image(sample_image_bytes, img, "test.jpg")  # Should not raise
