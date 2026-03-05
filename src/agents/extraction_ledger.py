"""
ExtractionLedger: Production-grade extraction logging for audit and traceability.

Logs every extraction event with strategy_used, confidence_score, cost_estimate, and processing_time.
Follows industry best practices for provenance and auditability in document intelligence pipelines.

Usage:
    ledger = ExtractionLedger(ledger_path)
    ledger.log_entry(doc_id, strategy, confidence, cost, processing_time, extra=None)
"""
import json
import time
from typing import Optional, Dict, Any
import os

class ExtractionLedger:
    def __init__(self, ledger_path: str = ".refinery/extraction_ledger.jsonl"):
        """
        Initialize ExtractionLedger with path to ledger file.
        Args:
            ledger_path: Path to the JSONL ledger file
        """
        self.ledger_path = ledger_path
        os.makedirs(os.path.dirname(ledger_path), exist_ok=True)

    def log_entry(
        self,
        doc_id: str,
        strategy: str,
        confidence: float,
        cost: float,
        processing_time: float,
        extra: Optional[Dict[str, Any]] = None,
    ):
        """
        Log an extraction event to the ledger.
        Args:
            doc_id: Document identifier
            strategy: Extraction strategy used
            confidence: Confidence score (0-1)
            cost: Estimated cost (USD)
            processing_time: Processing time in seconds
            extra: Optional additional metadata
        """
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "doc_id": doc_id,
            "strategy_used": strategy,
            "confidence_score": confidence,
            "cost_estimate": cost,
            "processing_time": processing_time,
        }
        if extra:
            entry.update(extra)
        with open(self.ledger_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
