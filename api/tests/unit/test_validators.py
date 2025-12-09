import pytest
import io
import base64
from PIL import Image

from app.utils.validators import (
    validate_image_count,
    decode_base64_image,
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
        assert "No images" in exc_info.value.message

    def test_too_many_images(self):
        """Test validation fails with too many images."""
        with pytest.raises(ImageValidationError) as exc_info:
            validate_image_count(["img"] * 6)
        assert "Too many images" in exc_info.value.message


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
