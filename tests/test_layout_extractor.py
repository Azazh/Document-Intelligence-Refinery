"""
Unit tests for LayoutExtractor (Strategy B).
Covers layout detection, extraction, and confidence scoring.
"""
import pytest
from src.strategies.layout_extractor import LayoutExtractor
import yaml
import os

def load_rules():
    with open("rubric/extraction_rules.yaml") as f:
        return yaml.safe_load(f)

@pytest.fixture
def rules():
    return load_rules()

@pytest.mark.parametrize("pdf_path", [
    "sample/mixed_CBE Annual Report 2017-18.pdf",
    "sample/digital_CBE Annual Report 2012-13.pdf",
])
def test_layout_extractor(pdf_path, rules):
    if not os.path.exists(pdf_path):
        pytest.skip(f"Sample PDF not found: {pdf_path}")
    extractor = LayoutExtractor(rules)
    result, confidence = extractor.extract(pdf_path)
    assert isinstance(result, dict)
    assert 0.0 <= confidence <= 1.0
    assert "pages" in result
    assert "layout_complexity" in result
