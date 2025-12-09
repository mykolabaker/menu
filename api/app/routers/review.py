from fastapi import APIRouter, HTTPException
import structlog

from ..models.requests import ReviewRequest
from ..models.responses import ProcessMenuResponse
from ..models.menu_item import VegetarianItem
from ..services.review_store import review_store

logger = structlog.get_logger()
router = APIRouter()


@router.post("/review", response_model=ProcessMenuResponse)
async def submit_review(body: ReviewRequest) -> ProcessMenuResponse:
    """
    Submit corrections for uncertain items (HITL).

    Takes the request_id from a previous needs_review response
    and user corrections for uncertain items.

    Returns the recomputed final result.
    """
    log = logger.bind(request_id=body.request_id)
    log.info("review_submitted", corrections_count=len(body.corrections))

    # Get stored result
    stored_result = review_store.get(body.request_id)
    if not stored_result:
        log.warning("review_not_found")
        raise HTTPException(
            status_code=404,
            detail=f"No pending review found for request_id: {body.request_id}",
        )

    # Build correction lookup
    corrections_map = {c.name.lower().strip(): c.is_vegetarian for c in body.corrections}

    # Start with confident vegetarian items
    vegetarian_items: list[VegetarianItem] = []

    # Add confident items
    for item in stored_result.get("confident_items", []):
        vegetarian_items.append(
            VegetarianItem(
                name=item["name"],
                price=item["price"],
                confidence=item.get("confidence", 1.0),
                reasoning=item.get("reasoning", "Previously classified with high confidence"),
            )
        )

    # Process uncertain items with corrections
    for item in stored_result.get("uncertain_items", []):
        item_key = item["name"].lower().strip()

        # Check if user provided correction
        if item_key in corrections_map:
            if corrections_map[item_key]:
                # User confirmed as vegetarian
                vegetarian_items.append(
                    VegetarianItem(
                        name=item["name"],
                        price=item["price"],
                        confidence=1.0,
                        reasoning="Confirmed vegetarian by human review",
                    )
                )
            # If false, we just don't add it
        else:
            # No correction provided, keep original uncertain state
            # Default to not including (conservative approach)
            pass

    # Calculate total
    total_sum = round(sum(item.price for item in vegetarian_items), 2)

    # Clean up store
    review_store.delete(body.request_id)

    log.info(
        "review_completed",
        vegetarian_count=len(vegetarian_items),
        total_sum=total_sum,
    )

    return ProcessMenuResponse(
        vegetarian_items=vegetarian_items,
        total_sum=total_sum,
    )
