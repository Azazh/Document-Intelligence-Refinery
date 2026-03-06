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

class FastTextExtractor:
    def __init__(self, rules: Dict[str, Any]):
        """
        Initialize FastTextExtractor with extraction rules.
        Args:
            rules: Dictionary of extraction thresholds (from extraction_rules.yaml)
        """
        self.rules = rules

    def extract(self, pdf_path: str) -> Tuple[Dict[str, Any], float]:
        """
        Extracts text and metadata from a PDF using pdfplumber.
        Computes a multi-signal confidence score and returns extraction result and confidence.
        Args:
            pdf_path: Path to the PDF file
        Returns:
            (result, confidence):
                result: Dict with extracted text, per-page stats, and metadata
                confidence: float (0-1) confidence score
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        with pdfplumber.open(pdf_path) as pdf:
            pages = []
            total_chars = 0
            total_area = 0
            total_images = 0
            fontnames = set()
            for page in pdf.pages:
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
                pages.append({
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
