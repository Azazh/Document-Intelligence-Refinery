"""
Unit tests for ExtractionLedger.
Covers logging and file output.
"""
import os
import json
import tempfile
from src.agents.extraction_ledger import ExtractionLedger

def test_extraction_ledger_log_entry():
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = os.path.join(tmpdir, "extraction_ledger.jsonl")
        ledger = ExtractionLedger(ledger_path)
        ledger.log_entry(
            doc_id="testdoc1",
            strategy="vision",
            confidence=0.92,
            cost=1.23,
            processing_time=2.5,
            extra={"custom": "meta"}
        )
        with open(ledger_path) as f:
            lines = f.readlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["doc_id"] == "testdoc1"
        assert entry["strategy_used"] == "vision"
        assert entry["confidence_score"] == 0.92
        assert entry["cost_estimate"] == 1.23
        assert entry["processing_time"] == 2.5
        assert entry["custom"] == "meta"
