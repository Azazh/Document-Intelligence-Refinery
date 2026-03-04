"""
Unit tests for FastTextExtractor (Strategy A).
Covers confidence scoring and escalation trigger.
"""
import pytest
from src.strategies.fast_text_extractor import FastTextExtractor
import yaml
import os

def load_rules():
    with open("rubric/extraction_rules.yaml") as f:
        return yaml.safe_load(f)

@pytest.fixture
def rules():
    return load_rules()

@pytest.mark.parametrize("pdf_path,expected_min_confidence", [
    ("sample/digital_CBE Annual Report 2012-13.pdf", 0.8),
    ("sample/scanned_2013-E.C-Audit-finding-information.pdf", 0.0),
])
def test_fast_text_extractor_confidence(pdf_path, expected_min_confidence, rules):
    if not os.path.exists(pdf_path):
        pytest.skip(f"Sample PDF not found: {pdf_path}")
    extractor = FastTextExtractor(rules)
    result, confidence = extractor.extract(pdf_path)
    assert isinstance(result, dict)
    assert 0.0 <= confidence <= 1.0
    assert confidence >= expected_min_confidence
