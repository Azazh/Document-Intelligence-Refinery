# Document Intelligence Pipeline: Implementation Approaches

## 1. PDF Origin Detection (Scanned vs. Digital)
**Current Approach:**
- Heuristic-based using character density and image-to-page ratio.
- If character density is low or image ratio is high, classify as scanned; otherwise, as digital or mixed.
- Fallback to OCR if pdfplumber fails to extract text.

**Industry Practice:**
- Start with heuristics (character density, image ratio).
- Use image analysis (bounding boxes, image area) for more accuracy.
- ML-based classification for large-scale or high-accuracy needs, using features like density, image ratio, and metadata.
- Always log ambiguous cases for review.

## 2. Text Extraction
**Current Approach:**
- Use pdfplumber for native PDFs.
- Fallback to OCR (pytesseract, PyMuPDF) for scanned or problematic PDFs.

**Industry Practice:**
- Hybrid extraction: try text extraction first, fallback to OCR.
- Use high-resolution images for OCR.
- Monitor extraction quality and log failures.

## 3. Domain Classification
**Current Approach:**
- YAML-configured, extensible keyword lists (with nested variants) for each domain.
- Fuzzy matching (rapidfuzz) for robust detection, especially with OCR noise.

**Industry Practice:**
- Start with keyword/phrase lists for explainability and rapid iteration.
- Add fuzzy/partial matching for noisy or scanned docs.
- Integrate ML/NLP models (e.g., BERT, spaCy) for high-volume or ambiguous cases.
- Hybrid: heuristics first, ML fallback.

## 4. Layout Complexity Detection
**Current Approach:**
- Simple heuristic: if page width > 800, classify as multi-column; else, single-column.

**Industry Practice:**
- Analyze text block positions (x-coordinates) to detect columns.
- Use clustering or histogram analysis of text positions.
- ML-based layout models (LayoutLM, Donut) for complex or high-value docs.

## 5. Pipeline Modularity & Extensibility
**Current Approach:**
- All config (rules, keywords) externalized in YAML for easy updates.
- Modular code structure (TriageAgent, main entry point, models).

**Industry Practice:**
- Modular, testable codebase.
- Config-driven for rapid adaptation.
- Logging, monitoring, and human-in-the-loop for continuous improvement.

---

# Next Steps (Planned/Recommended)
- Integrate ML-based classifiers for both origin and domain detection as labeled data grows.
- Add more advanced layout analysis (text block clustering, whitespace analysis).
- Enhance logging and reporting for monitoring and auditability.
- Build a feedback loop for human review of ambiguous or low-confidence cases.
- Continue to expand and refine YAML configs as new document types/domains are encountered.

---

*This documentation summarizes the current and industry-standard approaches for each major component of the pipeline, and can be used for technical reporting or presentations.*
