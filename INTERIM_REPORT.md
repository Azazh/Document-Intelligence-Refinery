# Document Intelligence Refinery: Interim Submission Report

## 1. Domain Notes (Phase 0 Deliverable)

### Extraction Strategy Decision Tree
Document Intelligence Refinery – Week 3 Interim Report

# 1. Domain Notes (Phase 0 Deliverable)

## 1.1 Extraction Strategy Decision Tree
Documents are routed through the pipeline based on their `DocumentProfile`, which includes fields such as `origin_type` (native_digital, scanned_image, mixed, form_fillable), `layout_complexity` (single_column, multi_column, table_heavy, figure_heavy, mixed), and an initial confidence score from the Triage Agent.

**Strategy Selection Logic (see `rubric/extraction_rules.yaml`):**

- **Native digital + single column** → FastTextExtractor (low cost, high speed)
- **Multi-column / table-heavy / mixed layout** → LayoutExtractor (medium cost, structure preserved)
- **Scanned image / low confidence from triage** → VisionExtractor (high cost, VLM, subject to budget cap)

An escalation guard monitors extraction confidence after each stage; if confidence falls below a threshold, the document is promoted to the next strategy. All thresholds and escalation logic are externally configurable.

**Explicit Digital vs. Scanned Criteria:**
- Digital: Character density > threshold, font metadata present, image area < 50% of page.
- Scanned: Character density ≈ 0, image area > 70%, no font metadata.

- **Routing:**
## 1.2 Failure Modes Observed (All Four Document Classes)

| Failure Mode         | Description                                                                 | Example (Named Corpus Doc) | Technical Cause / Observable Criteria |
|---------------------|-----------------------------------------------------------------------------|---------------------------|--------------------------------------|
| Structure collapse  | Tables/columns flattened, relationships lost                                | CBE ANNUAL REPORT 2023-24.pdf (Class A), tax_expenditure_ethiopia_2021_22.pdf (Class D) | FastTextExtractor on multi-column/table-heavy; low char density in table regions |
| Context poverty     | Related elements (e.g., table + caption) split into separate chunks          | fta_performance_survey_final_report_2022.pdf (Class C), tax_expenditure_ethiopia_2021_22.pdf (Class D) | Naive chunking, lack of LDU rules, missing parent/child linkage |
| Provenance blindness| Extracted data lacks page, bbox, or content_hash for audit                   | Audit Report - 2023.pdf (Class B), fta_performance_survey_final_report_2022.pdf (Class C) | Extractor omits spatial metadata; scanned images without OCR bbox |
| Escalation triggers | FastTextExtractor returns low-confidence/garbage on scanned or complex docs  | Audit Report - 2023.pdf (Class B) | Triage detects low char density, high image area, triggers escalation |
| Table OCR errors    | OCR misreads numbers, headers, or merges cells                               | Audit Report - 2023.pdf (Class B), tax_expenditure_ethiopia_2021_22.pdf (Class D) | VisionExtractor: VLM/OCR model errors, low image quality |
| Section misclassification | Headings missed, sections merged or split incorrectly                  | fta_performance_survey_final_report_2022.pdf (Class C) | LayoutExtractor: heading detection threshold too high/low |

**Observable Criteria for Document Type Detection:**
- Digital: High char density, font metadata, low image area, extractable text.
- Scanned: Low char density, high image area, no font metadata, image-only pages.
- Mixed: Alternating digital/scanned pages, variable char density.
- Table-heavy: >30% of page area covered by tables (detected via layout analysis).

### Failure Modes Observed
## 1.3 Pipeline Diagram (Mermaid)

flowchart TD
    A[Input Document (PDF, etc)] --> B[Triage Agent\n(DocumentProfile)]
    B -->|native_digital & single_column| C[FastTextExtractor\n(Low Cost, High Speed)]
    B -->|multi_column/table_heavy/mixed| D[LayoutExtractor\n(Medium Cost, Structure Preserved)]
    B -->|scanned_image or low confidence| E[VisionExtractor\n(High Cost, VLM, Budget Cap)]
    C -- Low Confidence --> D
    D -- Low Confidence --> E
    C & D & E --> F[Chunking Engine\n(LDU, Rules Enforced)]
    F --> G[PageIndex Builder\n(Hierarchical TOC)]
    G --> H[Query Agent\n(Provenance, Search, SQL)]
    H --> I[User/Downstream System]

    subgraph Audit & Provenance
      F
      G
      H
    end

    style F fill:#d0f0ff,stroke:#00796b,stroke-width:2px,color:#000
    style E fill:#ffd6cc,stroke:#b71c1c,stroke-width:2px,color:#000
    style D fill:#fff3b0,stroke:#f57f17,stroke-width:2px,color:#000
    style C fill:#d4edda,stroke:#1b5e20,stroke-width:2px,color:#000
    style B fill:#cfe2ff,stroke:#0d47a1,stroke-width:2px,color:#000
    style A fill:#eeeeee,stroke:#424242,stroke-width:2px,color:#000
    style G fill:#ead1ff,stroke:#6a1b9a,stroke-width:2px,color:#000
    style H fill:#ffd6e7,stroke:#880e4f,stroke-width:2px,color:#000
    style I fill:#ffffff,stroke:#212121,stroke-width:2px,color:#000
## 2. Architecture Diagram & Description

The system is built around a five-stage pipeline, each stage implemented as a modular, config-driven component:

| Stage | Component(s) | Responsibility |
|-------|--------------|---------------|
| 1. Triage Agent | DocumentProfile generator | Analyzes document properties (origin, layout complexity, etc.), assigns confidence score. Outputs Pydantic DocumentProfile. |
| 2. Structure Extraction Layer | FastTextExtractor, LayoutExtractor, VisionExtractor | Each implements BaseExtractor interface. Strategy pattern allows hot-swapping. Escalation guard routes low-confidence outputs to more powerful extractors. |
| 3. Semantic Chunking Engine | LDU (Logical Document Unit) builder | Applies chunking rules (preserve tables, captions, headings) and produces a list of LDU objects with embedded provenance. |
| 4. PageIndex Builder | Hierarchical index generator | Builds a tree of pages/sections (PageIndex) for navigation and retrieval. Stores content_hash for deduplication. |
| 5. Query Interface Agent | Provenance-aware search / SQL layer | Exposes query capabilities (keyword search, SQL over extracted data) and returns results with full provenance (page, bbox, document id). |

All stages share Pydantic schemas defined in `src/models/`. The pipeline is orchestrated by a central `ExtractionRouter` that reads configuration from `rubric/extraction_rules.yaml`.

    G --> H[Query Agent]
## 3. Cost Analysis (with Source Citations)


# 3. Cost Analysis (with Calculation Steps, Processing Time, and Class Variation)

Cost estimates are derived from the actual code logic and empirical runs. All costs and timings are logged in `.refinery/extraction_ledger.jsonl` for audit and traceability.

| Strategy         | Tool/Model                | Cost Tier | Est. Cost per Doc | Calculation Steps & Drivers | Processing Time (per doc) | Source/Justification |
|------------------|--------------------------|-----------|-------------------|---------------------------|--------------------------|---------------------|
| FastText         | pdfplumber               | Low       | ~$0.00            | 1 API call per page (local), negligible compute; e.g., 10 pages × 1 call = 10 calls | ~0.5–2s (10 pages)        | [pdfplumber docs](https://github.com/jsvine/pdfplumber) |
| LayoutExtractor  | Docling / MinerU         | Medium    | ~$0.01–$0.05      | 1 model inference per page (local), higher RAM/CPU; 10 pages × 1 = 10 inferences | ~2–8s (10 pages)          | [Docling](https://github.com/DS4SD/docling), [MinerU](https://github.com/opendatalab/MinerU) |
| VisionExtractor  | GPT-4o / Gemini VLM      | High      | $0.10–$2.00+      | 1 API call per page; token estimate: 2,000–4,000 tokens/page; 10 pages × $0.02–$0.20/page | ~10–60s (10 pages, API latency) | [OpenRouter pricing](https://openrouter.ai/pricing), [Gemini pricing](https://cloud.google.com/vertex-ai/pricing) |

**Calculation Example for VisionExtractor:**
- Assume 10-page scanned PDF, each page ~2,500 tokens (image-to-text prompt + output).
- OpenRouter GPT-4o: $5.00 per 1M tokens → $0.0125 per 2,500 tokens.
- 10 pages × $0.0125 = $0.125 (minimum, not including output tokens or retries).
- Gemini Vision: $0.02–$0.20 per page (varies by model and prompt size).

**Processing Time Estimates:**
- FastTextExtractor: ~0.05–0.2s per page (local, CPU-bound)
- LayoutExtractor: ~0.2–0.8s per page (local, model inference)
- VisionExtractor: ~1–6s per page (API call, network + model latency)

**Cost Variation by Document Class:**
- **Class A (Annual Financial Report, digital, multi-column):**
  - FastTextExtractor may be attempted, but LayoutExtractor is usually triggered due to layout complexity. Cost: ~$0.01–$0.05, time: 2–8s.
- **Class B (Scanned Government/Legal, image-based):**
  - VisionExtractor required for all pages. Cost: $0.10–$2.00+ (depends on page count and model), time: 10–60s.
- **Class C (Technical Assessment, mixed):**
  - Mixed routing: digital pages use FastText/Layout, scanned pages use Vision. Cost: $0.02–$0.50+, time: 3–20s.
- **Class D (Structured Data, table-heavy):**
  - LayoutExtractor preferred for table fidelity. Cost: ~$0.01–$0.05, time: 2–8s. If scanned, escalates to VisionExtractor.

**Budget Guard & Escalation Logic:**
- The ExtractionRouter checks a cumulative cost budget per document (e.g., $0.50, configurable in `extraction_rules.yaml`).
- If VisionExtractor would exceed the budget, the document is flagged for manual review instead of escalating.
- All costs, strategy choices, and confidence scores are logged in `.refinery/extraction_ledger.jsonl` for audit.

- **Stage 1:** Triage Agent (DocumentProfile)



## 4. Artifacts Checklist

All artifacts are located in the repository under the paths indicated.

| Artifact                        | Location                        | Status |
|---------------------------------|---------------------------------|--------|
| Pydantic schemas                | src/models/                     | ✅     |
| Triage Agent                    | src/agents/triage.py            | ✅     |
| FastTextExtractor               | src/strategies/fast_text_extractor.py | ✅ |
| LayoutExtractor                 | src/strategies/layout_extractor.py    | ✅ |
| VisionExtractor                 | src/strategies/vision_extractor.py    | ✅ |
| ExtractionRouter (escalation)   | src/agents/extractor.py         | ✅     |
| Centralized config              | rubric/extraction_rules.yaml    | ✅     |
| 12+ DocumentProfile JSONs       | .refinery/profiles/             | ✅     |
| Extraction ledger logs          | .refinery/extraction_ledger.jsonl| ✅    |
| Locked dependencies             | pyproject.toml, poetry.lock     | ✅     |
| README with setup/run           | README.md                       | ✅     |
| Unit tests for triage/extraction| tests/                          | 🟡 (80% coverage) |

| Metric                | Status/Notes                                                                                 |
## 6. Next Steps (for Final Submission)

- Expand PageIndex builder to support nested sections and robust heading detection.
- Implement query agent with natural language search over extracted chunks and SQL over tables.
- Add more real-world validation using documents from finance, healthcare, and legal domains.
- Improve test coverage to >90%, especially for edge cases in chunking and provenance.
- Refine chunking rules to better handle figures, captions, and multi-page tables.
- Prepare extraction quality analysis and document lessons learned in a final report.
| FDE Readiness         | All config in extraction_rules.yaml, new domains require config only, README for setup      |

---

## 5. Artifacts Checklist

- [x] `src/models/` — All Pydantic schemas (DocumentProfile, ExtractedDocument, LDU, PageIndex, ProvenanceChain)
- [x] `src/agents/triage.py` — Triage Agent
- [x] `src/strategies/` — FastTextExtractor, LayoutExtractor, VisionExtractor (shared interface)
- [x] `src/agents/extractor.py` — ExtractionRouter with escalation guard
- [x] `rubric/extraction_rules.yaml` — All config, thresholds, chunking rules
- [x] `.refinery/profiles/` — 12+ DocumentProfile JSONs
- [x] `.refinery/extraction_ledger.jsonl` — Extraction logs
- [x] `pyproject.toml` — Locked dependencies
- [x] `README.md` — Setup and run instructions
- [x] `tests/` — Unit tests for triage and extraction confidence

---

## 6. Next Steps

- Expand PageIndex builder and query agent
- Add more real-world validation and test coverage
- Refine chunking and audit logic
- Prepare final submission with extraction quality analysis and lessons learned
