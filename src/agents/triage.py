import os
import json
import uuid
from typing import Dict, Optional
from pathlib import Path
from pydantic import ValidationError
import pdfplumber
from src.models.document import DocumentProfile
import yaml
import pytesseract
from PIL import Image


class TriageAgent:
    def __init__(self, rules_path: str = "rubric/extraction_rules.yaml", keywords_path: str = "rubric/domain_keywords.yaml"):
        with open(rules_path, "r") as f:
            self.rules = yaml.safe_load(f)
        with open(keywords_path, "r") as f:
            self.domain_keywords = yaml.safe_load(f)

    def extract_text_with_ocr(self, pdf_path, min_text_length=30):
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text
            # If not enough text, use OCR
            if len(text.strip()) < min_text_length:
                text = ""
                for page in pdf.pages:
                    img = page.to_image(resolution=300).original
                    ocr_text = pytesseract.image_to_string(img)
                    text += ocr_text
        return text

    def analyze_pdf(self, pdf_path: str) -> Optional[DocumentProfile]:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                char_counts = []
                page_areas = []
                fontnames = set()
                for page in pdf.pages:
                    area = page.width * page.height
                    chars = page.chars
                    char_counts.append(len(chars))
                    page_areas.append(area)
                    for c in chars:
                        if "fontname" in c:
                            fontnames.add(c["fontname"])
                total_chars = sum(char_counts)
                total_area = sum(page_areas)
                char_density = total_chars / total_area if total_area > 0 else 0
                whitespace_ratio = self._estimate_whitespace(pdf)
                image_to_page_ratio = self._estimate_image_ratio(pdf)

                # Origin detection
                if char_density < self.rules["char_density_scanned"]:
                    origin_type = "scanned_image"
                elif image_to_page_ratio > self.rules["image_to_page_ratio_scanned"]:
                    origin_type = "scanned_image"
                elif char_density > self.rules["char_density_digital"]:
                    origin_type = "native_digital"
                else:
                    origin_type = "mixed"

                # Layout complexity
                layout_complexity = self._detect_layout_complexity(pdf)

                # Language (placeholder: ISO code)
                language = "en"

                # Use robust text extraction for domain hint
                text = self.extract_text_with_ocr(pdf_path)
                domain_hint = self._classify_domain_text(text)

                # Estimated cost
                if origin_type == "scanned_image":
                    estimated_cost_tier = "high"
                elif layout_complexity in ["multi_column", "table_heavy", "figure_heavy", "mixed"]:
                    estimated_cost_tier = "medium"
                else:
                    estimated_cost_tier = "low"

                extraction_metrics = {
                    "character_density": char_density,
                    "whitespace_ratio": whitespace_ratio,
                    "image_to_page_ratio": image_to_page_ratio
                }

                profile = DocumentProfile(
                    doc_id=uuid.uuid4(),
                    origin_type=origin_type,
                    layout_complexity=layout_complexity,
                    language=language,
                    domain_hint=domain_hint,
                    extraction_metrics=extraction_metrics,
                    estimated_cost_tier=estimated_cost_tier
                )
                self._save_profile(profile)
                return profile
        except (ValidationError, Exception) as e:
            print(f"Error analyzing {pdf_path}: {e}")
            return None

    def _estimate_whitespace(self, pdf) -> float:
        # Placeholder: mean whitespace ratio across pages
        ratios = []
        for page in pdf.pages:
            area = page.width * page.height
            chars = page.chars
            char_bboxes = [(
                float(c["x0"]), float(c["top"]), float(c["x1"]), float(c["bottom"])
            ) for c in chars]
            if char_bboxes:
                char_area = sum((x1-x0)*(b-y) for x0,y,x1,b in char_bboxes)
                whitespace = 1 - (char_area / area)
            else:
                whitespace = 1.0
            ratios.append(whitespace)
        return sum(ratios) / len(ratios) if ratios else 1.0

    def _estimate_image_ratio(self, pdf) -> float:
        # Placeholder: always 0 (extend with image detection if needed)
        return 0.0

    def _detect_layout_complexity(self, pdf) -> str:
        # Placeholder: use page width/height and char distribution
        # Extend with table/column detection heuristics
        if len(pdf.pages) > 0 and pdf.pages[0].width > 800:
            return "multi_column"
        return "single_column"

    def _classify_domain_text(self, text: str) -> str:
        text = text.lower()
        for domain, keyword_groups in self.domain_keywords.items():
            for group in keyword_groups:
                # Each group is a dict: {main_keyword: [variants]}
                if isinstance(group, dict):
                    for main_kw, variants in group.items():
                        # Check main keyword
                        if main_kw in text:
                            return domain
                        # Check all variants
                        for variant in variants:
                            if variant.lower() in text:
                                return domain
                # For backward compatibility: if group is a string
                elif isinstance(group, str):
                    if group in text:
                        return domain
        return "general"

    def _save_profile(self, profile: DocumentProfile):
        out_dir = Path(".refinery/profiles")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{profile.doc_id}.json"
        # Convert UUID to string for JSON serialization
        data = profile.dict()
        if isinstance(data.get("doc_id"), uuid.UUID):
            data["doc_id"] = str(data["doc_id"])
        try:
            with open(out_path, "w") as f:
                json.dump(data, f, indent=2)
            print(f"[DEBUG] Profile written: {out_path}")
        except Exception as e:
            print(f"[ERROR] Failed to write profile {out_path}: {e}")

