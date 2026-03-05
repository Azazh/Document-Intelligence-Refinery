
# RefineryAI: Document Intelligence Pipeline

RefineryAI is a production-grade, multi-stage agentic pipeline for unstructured document extraction and intelligence. It features classification-aware, spatially-indexed, provenance-preserving extraction, semantic chunking, and queryable knowledge for enterprise-scale document corpora.

---

## Features
- **Triage Agent:** Classifies documents by origin type, layout complexity, and domain hint.
- **Multi-Strategy Extraction:** FastText, Layout, and Vision extractors with confidence-gated escalation.
- **Semantic Chunking:** Converts raw extraction into logical document units (LDUs) for RAG.
- **PageIndex:** Builds a hierarchical navigation tree for efficient information retrieval.
- **Provenance & Auditability:** Every extraction is logged with strategy, confidence, cost, and processing time.
- **Configurable:** Extraction rules and thresholds are externalized in YAML.

## Project Structure
```
src/
  models/           # Pydantic schemas: DocumentProfile, ExtractedDocument, LDU, PageIndex, ProvenanceChain
  agents/           # Triage, ExtractionRouter, Chunker, Indexer, QueryAgent
  strategies/       # FastTextExtractor, LayoutExtractor, VisionExtractor
tests/              # Unit tests
.refinery/
  profiles/         # DocumentProfile JSON outputs
  extraction_ledger.jsonl  # Extraction event logs
rubric/             # extraction_rules.yaml and rubric files
pyproject.toml      # Locked dependencies
README.md           # This file
```


## GitHub Repository
Remote origin: https://github.com/Azazh/Document-Intelligence-Refinery.git

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/Azazh/Document-Intelligence-Refinery.git
cd Document-Intelligence-Refinery
```

### 2. Create and activate a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies (via Makefile)
```bash
make install
```

## Usage with Makefile

### Common tasks (via Makefile)

- **Install dependencies:**
	```bash
	make install
	```
- **Run the pipeline:**
	```bash
	make run
	# Edit src/main.py or pass arguments as needed
	```
- **Run all tests:**
	```bash
	make test
	```
- **Clean generated profiles:**
	```bash
	make clean
	```

## Running the Pipeline

**Usage:**
1. Place your PDFs or supported files in the `data/` directory.
2. Run the pipeline:
	```bash
	make run
	# or, for custom input:
	python src/main.py --input data/<your-document>.pdf
	```
	- Outputs: `.refinery/profiles/` (DocumentProfiles), `.refinery/extraction_ledger.jsonl` (extraction logs)

## Configuration
- **Extraction rules:** Edit `rubric/extraction_rules.yaml` to adjust chunking and extraction thresholds.

## Testing

Run all unit tests:
```bash
make test
```

## Output Artifacts
- `.refinery/profiles/`: DocumentProfile JSONs (at least 12, 3 per class)
- `.refinery/extraction_ledger.jsonl`: Extraction logs for the same documents

## Author
azazh-wuletawu

## License
No license specified. All rights reserved unless otherwise stated.
