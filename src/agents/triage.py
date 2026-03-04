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
from rapidfuzz import fuzz
import fitz  # PyMuPDF for robust fallback
import logging
import numpy as np
from sklearn.cluster import KMeans


try:
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class TriageAgent:
    # Set up a logger for ambiguous cases in a standardized logs/ directory
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    ambiguous_logger = logging.getLogger("ambiguous_cases")
    handler = logging.FileHandler(os.path.join(logs_dir, "ambiguous_cases.log"))
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    ambiguous_logger.addHandler(handler)
    ambiguous_logger.setLevel(logging.INFO)
    def __init__(self, rules_path: str = "rubric/extraction_rules.yaml", keywords_path: str = "rubric/domain_keywords.yaml"):
        """
        Initialize TriageAgent with YAML-configured extraction rules and domain keywords.
        Approach: Loads config files for flexible, config-driven pipeline behavior.
        Purpose: Centralize rules and keywords for document profiling.
        """
        with open(rules_path, "r") as f:
            self.rules = yaml.safe_load(f)
        with open(keywords_path, "r") as f:
            self.domain_keywords = yaml.safe_load(f)

    def extract_text_with_ocr(self, pdf_path, min_text_length=30):
        """
        Extracts text from PDF using pdfplumber; falls back to OCR if text is insufficient.
        Approach: Hybrid extraction—native text first, then OCR for scanned or problematic PDFs.
        Purpose: Maximize text extraction robustness for downstream analysis.
        """
        text = ""
        try:
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
        except Exception as e:
            print(f"[ERROR] pdfplumber failed on {pdf_path}: {e}. Using OCR fallback.")
            # OCR fallback for all pages if pdfplumber fails
            text = ""
            try:
                import fitz
                doc = fitz.open(pdf_path)
                for page in doc:
                    pix = page.get_pixmap(dpi=300)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    ocr_text = pytesseract.image_to_string(img)
                    text += ocr_text
            except Exception as ocr_e:
                print(f"[ERROR] OCR fallback also failed: {ocr_e}")
        return text

    def analyze_pdf(self, pdf_path: str) -> Optional[DocumentProfile]:
        """
        Main pipeline method: profiles a PDF document for origin, layout, domain, and extraction metrics.
        Approach: Combines heuristics, clustering, and fuzzy matching for robust document intelligence.
        Purpose: Generate a structured DocumentProfile for further processing or review.
        """
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
                char_density_scanned = self.rules["char_density_scanned"]
                char_density_digital = self.rules["char_density_digital"]
                image_to_page_ratio_scanned = self.rules["image_to_page_ratio_scanned"]
                ambiguous = False
                if char_density < char_density_scanned:
                    if image_to_page_ratio < image_to_page_ratio_scanned:
                        origin_type = "mixed"
                        ambiguous = True
                    else:
                        origin_type = "scanned_image"
                        if abs(char_density - char_density_scanned) < 0.1 * char_density_scanned:
                            ambiguous = True
                elif image_to_page_ratio > image_to_page_ratio_scanned:
                    origin_type = "scanned_image"
                    if abs(image_to_page_ratio - image_to_page_ratio_scanned) < 0.05:
                        ambiguous = True
                elif char_density > char_density_digital:
                    origin_type = "native_digital"
                    if abs(char_density - char_density_digital) < 0.1 * char_density_digital:
                        ambiguous = True
                else:
                    origin_type = "mixed"
                    ambiguous = True

                # Layout complexity
                layout_complexity = self._detect_layout_complexity(pdf)
                if layout_complexity == "multi_column" and pdf.pages[0].width < 900:
                    ambiguous = True

                # Language (placeholder: ISO code)
                language = "en"

                # Use robust text extraction for domain hint
                text = self.extract_text_with_ocr(pdf_path)
                domain_hint, domain_score = self._classify_domain_text_with_score(text)
                if domain_score < 90:
                    ambiguous = True

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

                # Log ambiguous cases
                if ambiguous:
                    self.ambiguous_logger.info(
                        f"Ambiguous classification for {pdf_path}: origin={origin_type}, char_density={char_density:.3f}, image_ratio={image_to_page_ratio:.3f}, domain={domain_hint} (score={domain_score}), layout={layout_complexity}"
                    )
                self._save_profile(profile)
                return profile
        except (ValidationError, Exception) as e:
            print(f"Error analyzing {pdf_path}: {e}")
            return None

    def _estimate_whitespace(self, pdf) -> float:
        """
        Estimates mean whitespace ratio across all pages in a PDF.
        Approach: Calculates whitespace by comparing character bounding box area to page area.
        Purpose: Support layout and complexity analysis.
        """
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
        """
        Calculates the ratio of image area to total page area in a PDF.
        Approach: Sums image bounding box areas and divides by total page area.
        Purpose: Support origin detection (scanned vs. digital).
        """
        total_image_area = 0
        total_page_area = 0
        for page in pdf.pages:
            total_page_area += page.width * page.height
            # pdfplumber page.images is a list of dicts with 'width' and 'height'
            for img in getattr(page, 'images', []):
                total_image_area += img.get('width', 0) * img.get('height', 0)
        return total_image_area / total_page_area if total_page_area > 0 else 0.0

    def _detect_layout_complexity(self, pdf) -> str:
        """
        Detects document layout complexity (single vs. multi-column) using clustering of x-coordinates of text blocks.
        Approach: Uses k-means clustering (if available) or histogram binning to find column structures based on text positions.
        Purpose: Robustly classify layout type for downstream document intelligence tasks.
        """
        # Cluster-based column detection using x-coordinates of text blocks
        all_x = []
        for page in pdf.pages:
            for c in page.chars:
                all_x.append(float(c["x0"]))
        if not all_x:
            return "single_column"
        x_array = np.array(all_x).reshape(-1, 1)

        # Try k-means clustering (2 clusters)
        if SKLEARN_AVAILABLE and len(x_array) >= 10:
            kmeans = KMeans(n_clusters=2, random_state=0).fit(x_array)
            centers = sorted([float(c) for c in kmeans.cluster_centers_.flatten()])
            # If cluster centers are far apart, it's multi-column
            page_width = pdf.pages[0].width if pdf.pages else 0
            if page_width > 0 and abs(centers[1] - centers[0]) > 0.3 * page_width:
                return "multi_column"
            else:
                return "single_column"
        else:
            # Fallback: histogram binning
            hist, bin_edges = np.histogram(x_array, bins=10)
            peaks = np.where(hist > 0.1 * max(hist))[0]
            if len(peaks) >= 2:
                return "multi_column"
            else:
                return "single_column"

    def _classify_domain_text_with_score(self, text: str, threshold: int = 85):
        """
        Classifies document domain using fuzzy matching against YAML-configured keywords.
        Approach: Returns best-matching domain and score using rapidfuzz partial ratio.
        Purpose: Robustly detect document domain, even with noisy or OCR text.
        """
        text = text.lower()
        best_score = 0
        best_domain = "general"
        for domain, keyword_groups in self.domain_keywords.items():
            for group in keyword_groups:
                if isinstance(group, dict):
                    for main_kw, variants in group.items():
                        # Exact match
                        if main_kw in text:
                            return domain, 100
                        # Fuzzy match for variants
                        for variant in variants:
                            score = fuzz.partial_ratio(variant.lower(), text)
                            if score > best_score:
                                best_score = score
                                best_domain = domain
                elif isinstance(group, str):
                    if group in text:
                        return domain, 100
                    score = fuzz.partial_ratio(group.lower(), text)
                    if score > best_score:
                        best_score = score
                        best_domain = domain
        return best_domain, best_score

    def _save_profile(self, profile: DocumentProfile):
        """
        Saves DocumentProfile as a JSON file in the profiles directory.
        Approach: Serializes profile and writes to disk for traceability and review.
        Purpose: Persist document intelligence results for downstream use.
        """
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

