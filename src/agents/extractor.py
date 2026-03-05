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
from src.strategies.layout_extractor import LayoutExtractor
from src.strategies.vision_extractor import VisionExtractor
from src.agents.extraction_ledger import ExtractionLedger

class ExtractionRouter:
    def __init__(self, rules: Dict[str, Any], ledger_path: str = ".refinery/extraction_ledger.jsonl"):
        """
        Initialize ExtractionRouter with extraction rules.
        Args:
            rules: Dictionary of extraction thresholds (from extraction_rules.yaml)
        """
        self.rules = rules
        self.fast_text = FastTextExtractor(rules)
        self.layout = LayoutExtractor(rules)
        self.vision = VisionExtractor(rules)
        self.ledger = ExtractionLedger(ledger_path)

    def extract(self, pdf_path: str, profile: Dict[str, Any], doc_id: str = None) -> Dict[str, Any]:
        """
        Route extraction based on DocumentProfile and confidence.
        Args:
            pdf_path: Path to PDF
            profile: DocumentProfile dict
        Returns:
            Extraction result dict (with strategy_used, confidence, etc.)
        """
        start_time = time.time()
        # Strategy A: FastTextExtractor
        if profile.get("origin_type") == "native_digital" and profile.get("layout_complexity") == "single_column":
            result, confidence = self.fast_text.extract(pdf_path)
            if confidence >= 0.8:
                elapsed = time.time() - start_time
                self.ledger.log_entry(doc_id or pdf_path, "fast_text", confidence, 0.0, elapsed)
                return {"strategy_used": "fast_text", "confidence": confidence, **result}
            # Escalate to layout extractor if low confidence
            layout_result, layout_conf = self.layout.extract(pdf_path)
            if layout_conf >= 0.7:
                elapsed = time.time() - start_time
                self.ledger.log_entry(doc_id or pdf_path, "layout", layout_conf, 0.0, elapsed)
                return {"strategy_used": "layout", "confidence": layout_conf, **layout_result}
            # Escalate to vision extractor if still low confidence
            vision_result, vision_conf, vision_cost = self.vision.extract(pdf_path)
            elapsed = time.time() - start_time
            self.ledger.log_entry(doc_id or pdf_path, "vision", vision_conf, vision_cost, elapsed)
            return {"strategy_used": "vision", "confidence": vision_conf, "cost": vision_cost, **vision_result}
        # Strategy B: LayoutExtractor for multi-column or table-heavy
        if profile.get("layout_complexity") in ["multi_column", "table_heavy", "mixed"] or profile.get("origin_type") == "mixed":
            result, confidence = self.layout.extract(pdf_path)
            if confidence >= 0.7:
                elapsed = time.time() - start_time
                self.ledger.log_entry(doc_id or pdf_path, "layout", confidence, 0.0, elapsed)
                return {"strategy_used": "layout", "confidence": confidence, **result}
            # Escalate to vision extractor if low confidence
            vision_result, vision_conf, vision_cost = self.vision.extract(pdf_path)
            elapsed = time.time() - start_time
            self.ledger.log_entry(doc_id or pdf_path, "vision", vision_conf, vision_cost, elapsed)
            return {"strategy_used": "vision", "confidence": vision_conf, "cost": vision_cost, **vision_result}
        # Strategy C: VisionExtractor for scanned_image or final fallback
        if profile.get("origin_type") == "scanned_image":
            vision_result, vision_conf, vision_cost = self.vision.extract(pdf_path)
            elapsed = time.time() - start_time
            self.ledger.log_entry(doc_id or pdf_path, "vision", vision_conf, vision_cost, elapsed)
            return {"strategy_used": "vision", "confidence": vision_conf, "cost": vision_cost, **vision_result}
        return {"strategy_used": "escalation_needed", "confidence": 0.0, "error": "No suitable strategy implemented yet."}
