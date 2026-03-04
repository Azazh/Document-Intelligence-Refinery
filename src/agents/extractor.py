"""
ExtractionRouter: Strategy pattern for multi-stage extraction.

Routes extraction requests to the appropriate strategy (FastText, Layout, Vision) based on DocumentProfile and confidence score.
Implements escalation guard: if confidence is low, escalates to next strategy.

Usage:
    router = ExtractionRouter(rules)
    result = router.extract(pdf_path, profile)
"""
from typing import Dict, Any
from src.strategies.fast_text_extractor import FastTextExtractor

class ExtractionRouter:
    def __init__(self, rules: Dict[str, Any]):
        """
        Initialize ExtractionRouter with extraction rules.
        Args:
            rules: Dictionary of extraction thresholds (from extraction_rules.yaml)
        """
        self.rules = rules
        self.fast_text = FastTextExtractor(rules)
        # TODO: Add layout and vision extractors

    def extract(self, pdf_path: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route extraction based on DocumentProfile and confidence.
        Args:
            pdf_path: Path to PDF
            profile: DocumentProfile dict
        Returns:
            Extraction result dict (with strategy_used, confidence, etc.)
        """
        # Strategy A: FastTextExtractor
        if profile.get("origin_type") == "native_digital" and profile.get("layout_complexity") == "single_column":
            result, confidence = self.fast_text.extract(pdf_path)
            if confidence >= 0.8:
                return {"strategy_used": "fast_text", "confidence": confidence, **result}
            # Escalate if low confidence
        # TODO: Add Strategy B (LayoutExtractor) and C (VisionExtractor)
        return {"strategy_used": "escalation_needed", "confidence": 0.0, "error": "No suitable strategy implemented yet."}
