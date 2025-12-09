import io
import time
from typing import Annotated
from fastapi import APIRouter, File, UploadFile, Request, HTTPException
from PIL import Image
import structlog

from ..config import get_settings
from ..models.requests import ProcessMenuBase64Request
from ..models.responses import ProcessMenuResponse, NeedsReviewResponse
from ..models.menu_item import MenuItem, VegetarianItem
from ..services.ocr_service import ocr_service
from ..services.text_parser import text_parser
from ..services.mcp_client import mcp_client
from ..services.review_store import review_store
from ..utils.validators import (
    validate_image_count,
    decode_base64_image,
    read_upload_file,
)
from ..utils.exceptions import (
    ImageValidationError,
    OCRError,
    MCPError,
    MCPUnavailableError,
)
from ..middleware.request_id import get_request_id

logger = structlog.get_logger()
router = APIRouter()


@router.post(
    "/process-menu",
    response_model=ProcessMenuResponse | NeedsReviewResponse,
    responses={
        400: {"description": "Invalid input"},
        422: {"description": "OCR failed"},
        500: {"description": "Internal server error"},
        503: {"description": "MCP server unavailable"},
    },
)
async def process_menu(
    request: Request,
    images: Annotated[list[UploadFile] | None, File()] = None,
    body: ProcessMenuBase64Request | None = None,
):
    """
    Process menu images and identify vegetarian dishes.

    Accepts either:
    - multipart/form-data with image files
    - application/json with base64-encoded images

    Returns:
    - List of vegetarian items and total sum
    - Or needs_review response if items have low confidence
    """
    request_id = get_request_id(request)
    log = logger.bind(request_id=request_id)

    start_time = time.time()

    try:
        # Get images from either source
        pil_images = await _get_images(images, body, request_id)

        log.info(
            "request_received",
            image_count=len(pil_images),
            timestamp=time.time(),
        )

        # Run OCR on all images
        ocr_texts = ocr_service.extract_text_batch(pil_images, request_id)

        # Check if we got any usable text
        total_text = "".join(ocr_texts)
        if not total_text.strip():
            raise OCRError(
                message="No text extracted",
                detail="OCR could not extract any readable text from the images",
            )

        # Parse text to extract menu items
        menu_items = text_parser.parse(ocr_texts, request_id)

        if not menu_items:
            # No items found, return empty result
            return ProcessMenuResponse(vegetarian_items=[], total_sum=0.0)

        # Call MCP server for classification
        mcp_result = await mcp_client.classify_and_calculate(menu_items, request_id)

        duration_ms = int((time.time() - start_time) * 1000)
        log.info("request_completed", duration_ms=duration_ms)

        # Handle needs_review response
        if mcp_result.get("status") == "needs_review":
            # Store for later review
            review_store.store(request_id, mcp_result)

            return NeedsReviewResponse(
                status="needs_review",
                request_id=request_id,
                confident_items=[
                    {"name": item["name"], "price": item["price"], "confidence": item["confidence"]}
                    for item in mcp_result.get("confident_items", [])
                ],
                uncertain_items=[
                    {
                        "name": item["name"],
                        "price": item["price"],
                        "confidence": item["confidence"],
                        "evidence": item.get("evidence", []),
                    }
                    for item in mcp_result.get("uncertain_items", [])
                ],
                partial_sum=mcp_result.get("partial_sum", 0.0),
            )

        # Return final result with confidence and reasoning
        return ProcessMenuResponse(
            vegetarian_items=[
                VegetarianItem(
                    name=item["name"],
                    price=item["price"],
                    confidence=item.get("confidence", 1.0),
                    reasoning=item.get("reasoning", ""),
                )
                for item in mcp_result.get("vegetarian_items", [])
            ],
            total_sum=mcp_result.get("total_sum", 0.0),
        )

    except ImageValidationError as e:
        log.warning("validation_error", error=e.message, detail=e.detail)
        raise HTTPException(status_code=400, detail=e.message)

    except OCRError as e:
        log.warning("ocr_error", error=e.message, detail=e.detail)
        raise HTTPException(status_code=422, detail=e.message)

    except MCPUnavailableError as e:
        log.error("mcp_unavailable", error=e.message)
        raise HTTPException(status_code=503, detail=e.message)

    except MCPError as e:
        log.error("mcp_error", error=e.message, detail=e.detail)
        raise HTTPException(status_code=500, detail=e.message)


async def _get_images(
    upload_files: list[UploadFile] | None,
    body: ProcessMenuBase64Request | None,
    request_id: str,
) -> list[Image.Image]:
    """Extract and validate images from request."""
    log = logger.bind(request_id=request_id)
    images: list[Image.Image] = []

    if upload_files:
        # Handle multipart upload
        validate_image_count(upload_files)

        for i, file in enumerate(upload_files):
            data, img = await read_upload_file(file)
            # Re-open image for processing
            images.append(Image.open(io.BytesIO(data)))

        log.debug("processed_multipart_images", count=len(images))

    elif body and body.images:
        # Handle base64 images
        validate_image_count(body.images)

        for i, b64_str in enumerate(body.images):
            data, img = decode_base64_image(b64_str, i)
            # Re-open image for processing
            images.append(Image.open(io.BytesIO(data)))

        log.debug("processed_base64_images", count=len(images))

    else:
        raise ImageValidationError(
            message="No images provided",
            detail="Request must include 'images' as files or base64 strings",
        )

    return images
