#
# Vision Extraction (Strategy C)

## Approach
- Use a multimodal vision-language model (e.g., OpenRouter, Gemini, GPT-4o) to extract text, tables, and figures from page images.
- Accepts page images and structured extraction prompts for high-fidelity extraction.
- Implements a budget_guard: tracks token/cost per document and enforces a configurable budget cap.
- Escalates only when fast text and layout strategies are insufficient or for scanned_image documents.

## Rationale
- Vision models outperform OCR and layout heuristics on complex, scanned, or handwritten documents.
- Budget guard is critical for production cost control (industry best practice: always cap per-document spend).
- Follows industry practice: production pipelines (Google Document AI, ABBYY Vantage, etc.) use vision models as final fallback.

## Best Practices
- Use vision extraction only when necessary (scanned, low-confidence, or failed layout extraction).
- Track and log cost per document for audit and optimization.
- Regularly review extraction quality and cost tradeoffs.

## Thresholds
- See extraction_rules.yaml for all vision-related thresholds and budget caps.

## Continuous Validation
- Monitor cost and extraction quality, and update budget caps and escalation logic as needed.
#
# Layout Extraction (Strategy B)

## Approach
- Use pdfplumber to extract text blocks with bounding boxes, tables, and figures.
- Detect multi-column layouts using clustering (KMeans) on x0 positions of text blocks.
- Extract tables as structured JSON and figures as image metadata.
- Confidence scoring based on layout complexity and block count.

## Rationale
- Multi-column and table-heavy layouts require spatially-aware extraction for fidelity.
- Clustering is a lightweight, production-friendly alternative to full layout models for most business documents.
- Follows industry practice: ABBYY, Kofax, and open-source frameworks use similar heuristics for layout detection.

## Best Practices
- Tune clustering and block thresholds empirically on real documents.
- Use layout-aware extraction for all non-single-column or ambiguous cases.
- Escalate to vision models only if layout extraction confidence is low or fails.

## Thresholds
- See extraction_rules.yaml for all layout-related thresholds.

## Continuous Validation
- Regularly review layout extraction results and update rules as new document types are encountered.
# DOMAIN_NOTES.md

## Phase 0: Extraction Strategy Decision Tree, Failure Modes, and Pipeline Diagram


### 1. Phase 0 Workflow Overview

**Document Type Classification:**
- Use pdfplumber to analyze each PDF for:
  - Character density (chars/page area)
  - Whitespace ratio
  - Bbox variance
- Classify as:
  - **digital**: High character density, low whitespace
  - **scanned**: Near-zero character density, high whitespace
  - **mixed**: Intermediate or highly variable metrics

**Processing:**
- All PDFs are analyzed by pdfplumber.
- Only digital and scanned PDFs are processed by Docling.
- Mixed PDFs are skipped for Docling due to repeated timeouts and failures.
- There is no extraction router or escalation logic in this phase—each tool runs independently on the allowed types.


### 2. Failure Modes Observed

- **pdfplumber**
  - Fails to extract text from scanned PDFs (character density = 0, whitespace = 1.0)
  - May misinterpret complex layouts (tables, multi-column)
  - Bounding box variance is low for scanned, higher for digital
- **Docling**
  - Handles digital and scanned PDFs, but may not detect tables in simple layouts
  - For scanned PDFs, output is often empty or only detects images/structure, not text
  - For mixed PDFs, Docling repeatedly times out or fails to produce output, so these are skipped entirely in this phase.


### 3. Phase 0 Pipeline Diagram (Mermaid)

```
graph TD
  A[PDF Input] --> B[pdfplumber Analysis]
  A --> C{Type?}
  C -->|digital| D[Docling Analysis]
  C -->|scanned| D
  C -->|mixed| E[Skip Docling (Timeout)]
  B --> F[PDFPlumber Results]
  D --> G[Docling Results]
  E --> H[No Docling Output]
```


### 4. Summary of Phase 0 Outputs

- All sample PDFs analyzed with pdfplumber; results in `pdfplumber_results.json`.
- Digital and scanned PDFs processed with Docling; results in `docling_full_results.json`.
- All results merged in `merged_results.json` for easy comparison.
- Quality comparison report generated for digital and scanned types.
- Mixed PDFs are skipped for Docling due to timeouts/failures.


### 5. Comparison Results Summary (Docling vs. pdfplumber)

**Digital PDF (digital_CBE Annual Report 2012-13.pdf):**
- pdfplumber: Successfully extracted text, character density and bbox variance indicate digital origin. No tables detected by Docling.
- Docling: No tables detected; output is minimal for this simple layout.

**Scanned PDF (scanned_2013-E.C-Audit-finding-information.pdf):**
- pdfplumber: Failed to extract text (character density = 0, whitespace = 1.0), confirming scanned nature.
- Docling: No tables detected; output is minimal, mostly structure/images.

**Mixed PDF:**
- Skipped for Docling due to repeated timeouts/failures.

---

*This document summarizes the Phase 0 onboarding, extraction decision logic, observed tool failure modes, a pipeline diagram, and a summary of comparative results as required.*
