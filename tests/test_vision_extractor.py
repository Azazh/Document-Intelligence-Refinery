"""
Unit tests for VisionExtractor (Strategy C).
Covers budget guard, extraction, and confidence scoring.
"""
import pytest
from src.strategies.vision_extractor import VisionExtractor
import yaml
import os

def load_rules():
    with open("rubric/extraction_rules.yaml") as f:
        return yaml.safe_load(f)

@pytest.fixture
def rules():
    return load_rules()

@pytest.mark.parametrize("pdf_path,budget_cap,expect_budget_exceeded", [
    ("sample/scanned_2013-E.C-Audit-finding-information.pdf", 2.0, False),
    ("sample/scanned_2013-E.C-Audit-finding-information.pdf", 0.5, True),
])
def test_vision_extractor_budget(pdf_path, budget_cap, expect_budget_exceeded, rules):
    if not os.path.exists(pdf_path):
        pytest.skip(f"Sample PDF not found: {pdf_path}")
    extractor = VisionExtractor(rules, budget_cap=budget_cap)
    result, confidence, cost = extractor.extract(pdf_path)
    if expect_budget_exceeded:
        assert "error" in result and "Budget cap" in result["error"]
    else:
        assert isinstance(result, dict)
        assert 0.0 <= confidence <= 1.0
        assert cost <= budget_cap
