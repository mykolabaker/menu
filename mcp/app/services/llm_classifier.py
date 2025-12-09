import json
import os
import time
import ollama
import structlog

from ..config import get_settings
from ..models.classification import LLMClassificationResponse, RAGEvidence

logger = structlog.get_logger()

# Configure Langsmith if API key is set
_settings = get_settings()
if _settings.langsmith_api_key:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = _settings.langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = _settings.langsmith_project


def _trace_llm_call(func):
    """Decorator to trace LLM calls with Langsmith when enabled."""
    def wrapper(*args, **kwargs):
        settings = get_settings()
        if not settings.langsmith_api_key:
            return func(*args, **kwargs)

        try:
            from langsmith import traceable

            @traceable(name="llm_classify", run_type="llm")
            def traced_func(*a, **kw):
                return func(*a, **kw)

            return traced_func(*args, **kwargs)
        except ImportError:
            return func(*args, **kwargs)

    return wrapper


CLASSIFICATION_PROMPT = """You are a vegetarian dish classifier. Analyze the following dish and determine if it is vegetarian.

Dish name: {dish_name}
{description_section}
{evidence_section}

IMPORTANT RULES:
- Vegetarian means NO meat, poultry, fish, or seafood
- Eggs and dairy ARE acceptable for vegetarian dishes
- If you're unsure, be conservative and mark as non-vegetarian
- Consider the dish name carefully - some names are misleading

Respond with ONLY valid JSON in this exact format:
{{
  "is_vegetarian": true or false,
  "confidence": 0.0 to 1.0,
  "reasoning": "Brief explanation in one sentence"
}}"""


class LLMClassifier:
    """LLM-based vegetarian classification using Ollama."""

    def __init__(self):
        self.settings = get_settings()
        self.client = ollama.Client(host=self.settings.ollama_base_url)

    def classify(
        self,
        dish_name: str,
        description: str | None = None,
        rag_evidence: list[RAGEvidence] | None = None,
        request_id: str = "",
    ) -> LLMClassificationResponse | None:
        """
        Classify a dish using the LLM.

        Args:
            dish_name: Name of the dish
            description: Optional description
            rag_evidence: Optional evidence from RAG system
            request_id: Request ID for logging

        Returns:
            LLMClassificationResponse or None if LLM fails
        """
        log = logger.bind(request_id=request_id, dish_name=dish_name)

        # Build prompt
        prompt = self._build_prompt(dish_name, description, rag_evidence)

        start_time = time.time()

        try:
            response = self.client.chat(
                model=self.settings.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that classifies dishes as vegetarian or non-vegetarian. Always respond with valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                options={
                    "temperature": 0.1,  # Low temperature for consistent results
                },
            )

            duration_ms = int((time.time() - start_time) * 1000)

            # Extract content
            content = response["message"]["content"]

            log.info(
                "llm_call",
                model=self.settings.llm_model,
                duration_ms=duration_ms,
            )

            # Parse response
            return self._parse_response(content, log)

        except Exception as e:
            log.error("llm_call_failed", error=str(e))
            return None

    def _build_prompt(
        self,
        dish_name: str,
        description: str | None,
        rag_evidence: list[RAGEvidence] | None,
    ) -> str:
        """Build the classification prompt."""
        description_section = ""
        if description:
            description_section = f"Description: {description}"

        evidence_section = ""
        if rag_evidence:
            evidence_lines = ["Similar dishes from our database:"]
            for ev in rag_evidence[:3]:  # Top 3 evidence items
                veg_status = "vegetarian" if ev.is_vegetarian else "non-vegetarian"
                evidence_lines.append(f"- {ev.dish_name} ({veg_status}, similarity: {ev.similarity_score:.2f})")
            evidence_section = "\n".join(evidence_lines)

        return CLASSIFICATION_PROMPT.format(
            dish_name=dish_name,
            description_section=description_section,
            evidence_section=evidence_section,
        )

    def _parse_response(self, content: str, log) -> LLMClassificationResponse | None:
        """Parse LLM response JSON."""
        try:
            # Try to extract JSON from response
            # Sometimes LLM wraps JSON in markdown code blocks
            content = content.strip()
            if content.startswith("```"):
                # Remove markdown code blocks
                lines = content.split("\n")
                content = "\n".join(lines[1:-1])

            data = json.loads(content)

            return LLMClassificationResponse(
                is_vegetarian=bool(data.get("is_vegetarian", False)),
                confidence=float(data.get("confidence", 0.5)),
                reasoning=str(data.get("reasoning", "No reasoning provided")),
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            log.warning("llm_response_parse_failed", error=str(e), content=content[:200])
            return None

    def is_available(self) -> bool:
        """Check if LLM service is available."""
        try:
            self.client.list()
            return True
        except Exception:
            return False


# Singleton instance
llm_classifier = LLMClassifier()
