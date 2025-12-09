import time
import structlog

from ..config import get_settings
from ..models.tool_input import ClassifyAndCalculateInput, MenuItemInput
from ..models.tool_output import (
    ClassifyAndCalculateOutput,
    NeedsReviewOutput,
    VegetarianItemOutput,
    UncertainItemOutput,
)
from ..models.classification import ClassificationResult
from ..services.llm_classifier import llm_classifier
from ..services.keyword_classifier import keyword_classifier
from ..services.rag_service import rag_service
from ..services.calculator import calculator

logger = structlog.get_logger()


class ClassifyAndCalculateTool:
    """
    Main tool for classifying menu items and calculating totals.

    Combines RAG, LLM, and keyword classification for robust results.
    """

    def __init__(self):
        self.settings = get_settings()

    async def execute(
        self, input_data: ClassifyAndCalculateInput
    ) -> ClassifyAndCalculateOutput | NeedsReviewOutput:
        """
        Execute the classification and calculation.

        Args:
            input_data: Input containing menu items and request_id

        Returns:
            Either final results or needs_review response
        """
        log = logger.bind(request_id=input_data.request_id)
        log.info("classification_started", items_count=len(input_data.menu_items))

        start_time = time.time()

        # Classify each item
        classifications: list[tuple[MenuItemInput, ClassificationResult]] = []

        for item in input_data.menu_items:
            result = self._classify_item(item, input_data.request_id)
            classifications.append((item, result))

        # Separate confident and uncertain items
        confident_veg: list[VegetarianItemOutput] = []
        uncertain: list[UncertainItemOutput] = []

        for item, classification in classifications:
            if classification.is_vegetarian:
                if classification.confidence >= self.settings.confidence_threshold:
                    confident_veg.append(
                        VegetarianItemOutput(
                            name=item.name,
                            price=item.price,
                            confidence=classification.confidence,
                            reasoning=classification.reasoning,
                        )
                    )
                else:
                    uncertain.append(
                        UncertainItemOutput(
                            name=item.name,
                            price=item.price,
                            confidence=classification.confidence,
                            evidence=[classification.reasoning],
                        )
                    )
            else:
                # Non-vegetarian with low confidence should also be flagged
                if classification.confidence < self.settings.confidence_threshold:
                    uncertain.append(
                        UncertainItemOutput(
                            name=item.name,
                            price=item.price,
                            confidence=classification.confidence,
                            evidence=[classification.reasoning],
                        )
                    )

        duration_ms = int((time.time() - start_time) * 1000)
        vegetarian_total = calculator.calculate_total(
            [{"price": item.price} for item in confident_veg],
            input_data.request_id,
        )

        log.info(
            "classification_completed",
            vegetarian_count=len(confident_veg),
            uncertain_count=len(uncertain),
            total_sum=vegetarian_total,
            duration_ms=duration_ms,
        )

        # Return appropriate response
        if uncertain:
            partial_sum = vegetarian_total
            return NeedsReviewOutput(
                status="needs_review",
                request_id=input_data.request_id,
                confident_items=confident_veg,
                uncertain_items=uncertain,
                partial_sum=partial_sum,
            )

        return ClassifyAndCalculateOutput(
            vegetarian_items=confident_veg,
            total_sum=vegetarian_total,
            request_id=input_data.request_id,
        )

    def _classify_item(
        self, item: MenuItemInput, request_id: str
    ) -> ClassificationResult:
        """
        Classify a single menu item using combined approach.

        Priority:
        1. RAG evidence for context
        2. LLM classification (primary)
        3. Keyword fallback
        4. Combine signals for final decision
        """
        log = logger.bind(request_id=request_id, dish_name=item.name)

        # Step 1: Get RAG evidence
        rag_evidence = rag_service.search(
            query=item.name,
            request_id=request_id,
        )

        # Step 2: Try LLM classification with RAG context
        llm_result = llm_classifier.classify(
            dish_name=item.name,
            description=item.description,
            rag_evidence=rag_evidence,
            request_id=request_id,
        )

        # Step 3: Get keyword classification
        keyword_result = keyword_classifier.classify(
            dish_name=item.name,
            description=item.description,
        )

        # Step 4: Combine results
        return self._combine_classifications(
            llm_result=llm_result,
            keyword_result=keyword_result,
            rag_evidence=rag_evidence,
            log=log,
        )

    def _combine_classifications(
        self,
        llm_result,
        keyword_result,
        rag_evidence,
        log,
    ) -> ClassificationResult:
        """Combine classification signals into final decision."""

        # If LLM succeeded, use it as primary
        if llm_result:
            # Check for conflicts with strong keyword signal
            if (
                keyword_result.confidence >= 0.8
                and keyword_result.is_vegetarian is not None
                and keyword_result.is_vegetarian != llm_result.is_vegetarian
            ):
                # Keyword strongly disagrees, reduce confidence
                log.debug(
                    "classification_conflict",
                    llm=llm_result.is_vegetarian,
                    keyword=keyword_result.is_vegetarian,
                )
                return ClassificationResult(
                    is_vegetarian=llm_result.is_vegetarian,
                    confidence=min(llm_result.confidence, 0.6),
                    reasoning=f"{llm_result.reasoning} (Note: keyword analysis suggests otherwise)",
                    method="combined",
                )

            # LLM result is primary
            # Boost confidence if RAG agrees
            confidence = llm_result.confidence
            if rag_evidence:
                top_match = rag_evidence[0]
                if (
                    top_match.similarity_score > 0.7
                    and top_match.is_vegetarian == llm_result.is_vegetarian
                ):
                    confidence = min(confidence + 0.1, 1.0)

            return ClassificationResult(
                is_vegetarian=llm_result.is_vegetarian,
                confidence=round(confidence, 2),
                reasoning=llm_result.reasoning,
                method="llm+rag",
            )

        # LLM failed, use keyword as fallback
        if keyword_result.is_vegetarian is not None:
            log.debug("using_keyword_fallback")
            return ClassificationResult(
                is_vegetarian=keyword_result.is_vegetarian,
                confidence=keyword_result.confidence,
                reasoning=f"Keyword match: {', '.join(keyword_result.matched_keywords)}",
                method="keyword",
            )

        # No clear signal, use RAG if available
        if rag_evidence and rag_evidence[0].similarity_score > 0.8:
            top_match = rag_evidence[0]
            log.debug("using_rag_fallback", match=top_match.dish_name)
            return ClassificationResult(
                is_vegetarian=top_match.is_vegetarian,
                confidence=top_match.similarity_score * 0.8,
                reasoning=f"Similar to known dish: {top_match.dish_name}",
                method="rag",
            )

        # Default: uncertain, mark as non-vegetarian to be safe
        log.debug("classification_uncertain")
        return ClassificationResult(
            is_vegetarian=False,
            confidence=0.3,
            reasoning="Unable to determine with confidence, defaulting to non-vegetarian",
            method="default",
        )


# Singleton instance
classify_and_calculate_tool = ClassifyAndCalculateTool()
