import os
import uuid
import shutil
import pytest
from src.agents.triage import TriageAgent
from src.models.document import DocumentProfile

def test_triage_agent_on_sample_pdf(tmp_path):
    # Arrange
    agent = TriageAgent()
    sample_dir = "/home/azazh-wuletawu/Documents/10x Intensive Training/W3/code_implementation/RefineryAI-Document-Intelligence-Pipeline/sample"
    pdf_files = [
        os.path.join(sample_dir, f)
        for f in os.listdir(sample_dir)
        if f.lower().endswith(".pdf")
    ]
    if not pdf_files:
        pytest.skip("No PDF files found in sample directory")

    for pdf_path in pdf_files:
        profile = agent.analyze_pdf(pdf_path)
        assert profile is not None, f"Profile is None for {pdf_path}"
        assert isinstance(profile, DocumentProfile)
        assert profile.origin_type in {"scanned_image", "native_digital", "mixed"}
        assert profile.layout_complexity in {"single_column", "multi_column"}
        assert profile.estimated_cost_tier in {"low", "medium", "high"}
        # Check profile persistence
        out_path = f".refinery/profiles/{profile.doc_id}.json"
        assert os.path.exists(out_path)
        # Clean up
        os.remove(out_path)

def test_triage_agent_handles_invalid_pdf(tmp_path):
    agent = TriageAgent()
    # Create a dummy file
    dummy_path = tmp_path / "not_a_pdf.pdf"
    with open(dummy_path, "w") as f:
        f.write("not a real pdf")
    profile = agent.analyze_pdf(str(dummy_path))
    assert profile is None

def test_triage_agent_extensible_rules(tmp_path):
    # Custom rules file
    custom_rules = tmp_path / "custom_rules.yaml"
    custom_rules.write_text("""
char_density_scanned: 0.00001
char_density_digital: 0.1
image_to_page_ratio_scanned: 0.9
""")
    agent = TriageAgent(rules_path=str(custom_rules))
    # Should still work with missing/invalid PDF
    dummy_path = tmp_path / "not_a_pdf.pdf"
    with open(dummy_path, "w") as f:
        f.write("not a real pdf")
    profile = agent.analyze_pdf(str(dummy_path))
    assert profile is None
