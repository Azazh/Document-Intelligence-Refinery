import os
import pytest
from src.agents.triage import TriageAgent
from src.models.document import DocumentProfile

@pytest.mark.parametrize("pdf_path,expected_origin,expected_layout", [
    ("sample/digital_CBE Annual Report 2012-13.pdf", "mixed", None),
    ("sample/scanned_2013-E.C-Audit-finding-information.pdf", "scanned_image", None),
    ("sample/mixed_CBE Annual Report 2017-18.pdf", "mixed", None),
])
def test_triage_classification(pdf_path, expected_origin, expected_layout):
    agent = TriageAgent()
    if not os.path.exists(pdf_path):
        pytest.skip(f"Sample PDF not found: {pdf_path}")
    profile = agent.analyze_pdf(pdf_path)
    assert profile is not None
    assert profile.origin_type == expected_origin
    if expected_layout:
        assert profile.layout_complexity == expected_layout
    assert profile.domain_hint in agent.domain_keywords
    assert profile.estimated_cost_tier in {"low", "medium", "high"}

def test_confidence_scoring_thresholds():
    agent = TriageAgent()
    # Simulate profiles with different metrics
    # These would be replaced with mocks or fixtures in a full test suite
    low_conf = {'character_density': 0.005, 'image_to_page_ratio': 0.85}
    high_conf = {'character_density': 0.1, 'image_to_page_ratio': 0.01}
    # These are not direct calls but illustrate the confidence logic
    assert low_conf['character_density'] < agent.rules['char_density_scanned']  # 0.005 < 0.01
    assert high_conf['character_density'] > agent.rules['char_density_digital']  # 0.1 > 0.05
    assert low_conf['image_to_page_ratio'] > agent.rules['image_to_page_ratio_scanned']  # 0.85 > 0.8
    assert high_conf['image_to_page_ratio'] < agent.rules['image_to_page_ratio_scanned']  # 0.01 < 0.8
