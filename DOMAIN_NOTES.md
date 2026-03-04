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
