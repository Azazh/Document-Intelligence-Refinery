"""
FastTextExtractor: Production-grade fast text extraction for digital PDFs.

Implements a confidence-gated extraction strategy using pdfplumber, following industry best practices:
- Multi-signal confidence scoring (character count, density, image ratio, font metadata)
- Escalates to layout/vision model if confidence is low
- Modular, clean, and extensible for real-world pipelines

Usage:
    extractor = FastTextExtractor(rules)
    result, confidence = extractor.extract(pdf_path)
"""
import pdfplumber
from typing import Dict, Any, Tuple
import os
from src.strategies.base_extractor import BaseExtractor
from uuid import uuid4

class FastTextExtractor(BaseExtractor):
    def extract(self, pdf_path: str) -> Tuple[Dict[str, Any], float]:
        """
        Extracts text and metadata from a PDF using pdfplumber.
        Computes a multi-signal confidence score and returns extraction result and confidence.
        All thresholds and weights are loaded from config.
        Output is normalized to ExtractedDocument/LDU schema.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        with pdfplumber.open(pdf_path) as pdf:
            ldu_list = []
            total_chars = 0
            total_area = 0
            total_images = 0
            fontnames = set()
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                char_count = len(text)
                total_chars += char_count
                area = page.width * page.height
                total_area += area
                images = page.images or []
                total_images += len(images)
                # Font metadata
                try:
                    chars = page.chars
                    for c in chars:
                        fontnames.add(c.get("fontname", ""))
                except Exception:
                    pass
                ldu_list.append({
                    "ldu_id": str(uuid4()),
                    "content": text,
                    "chunk_type": "text",
                    "page_refs": [i+1],
                    "bounding_box": None,
                    "parent_section": None,
                    "token_count": len(text.split()),
                    "content_hash": str(hash(text)),
                    "metadata": {"char_count": char_count, "area": area, "image_count": len(images)}
                })
            char_density = total_chars / total_area if total_area > 0 else 0
            image_ratio = total_images / len(pdf.pages) if pdf.pages else 0
            font_metadata_present = len(fontnames) > 0
            # Config-driven confidence scoring
            weights = self.rules.get("confidence_weights", {})
            conf = 1.0
            if char_density < self.rules.get("char_density_digital", 0.07):
                conf *= 1 - weights.get("char_density", 0.3)
            if image_ratio > self.rules.get("image_to_page_ratio_digital", 0.15):
                conf *= 1 - weights.get("image_ratio", 0.2)
            if not font_metadata_present:
                conf *= 1 - weights.get("font_metadata", 0.2)
            if total_chars < 100 * len(pdf.pages):
                conf *= 0.5
            result = {
                "extracted_document": {
                    "doc_id": str(uuid4()),
                    "text_blocks": ldu_list,
                    "tables": [],
                    "figures": [],
                    "reading_order": [ldu["ldu_id"] for ldu in ldu_list]
                },
                "char_density": char_density,
                "image_ratio": image_ratio,
                "font_metadata_present": font_metadata_present
            }
            return result, conf
                    "text": text,
                    "char_count": char_count,
                    "area": area,
                    "image_count": len(images),
                })
            char_density = total_chars / total_area if total_area > 0 else 0
            image_ratio = total_images / len(pdf.pages) if pdf.pages else 0
            font_metadata_present = len(fontnames) > 0
            # Confidence scoring (production-style)
            conf = 1.0
            if char_density < self.rules.get("char_density_digital", 0.07):
                conf *= 0.5
            if image_ratio > self.rules.get("image_to_page_ratio_digital", 0.15):
                conf *= 0.5
            if not font_metadata_present:
                conf *= 0.7
            if total_chars < 100 * len(pdf.pages):
                conf *= 0.5
            result = {
                "pages": pages,
                "char_density": char_density,
                "image_ratio": image_ratio,
                "font_metadata_present": font_metadata_present,
                "total_chars": total_chars,
                "total_images": total_images,
            }
            return result, conf
