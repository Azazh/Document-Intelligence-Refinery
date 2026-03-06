import os
import argparse
import yaml
import json
import traceback
from src.agents.triage import TriageAgent
from src.agents.extractor import ExtractionRouter
from src.agents.chunker import ChunkingEngine
from src.agents.indexer import PageIndexBuilder

def main():
    sample_dir = "./sample"
    parser = argparse.ArgumentParser(description="Run full pipeline: profiling and extraction on sample PDFs.")
    parser.add_argument(
        "--dir", type=str, default=sample_dir,
        help="Directory containing PDF files to process (default: ./sample)"
    )
    args = parser.parse_args()

    # Phase 1: Profiling
    agent = TriageAgent()
    pdf_files = [
        os.path.join(args.dir, f)
        for f in os.listdir(args.dir)
        if f.lower().endswith(".pdf")
    ]
    print(f"[INFO] Found {len(pdf_files)} PDF(s) in {args.dir}")
    if not pdf_files:
        print(f"[ERROR] No PDF files found in {args.dir}")
        return

    for pdf_path in pdf_files:
        try:
            print(f"[INFO] Profiling: {pdf_path}")
            profile = agent.analyze_pdf(pdf_path)
            if profile:
                print(f"[INFO] Profile saved for {pdf_path} (doc_id={profile.doc_id})")
            else:
                print(f"[WARN] Failed to process {pdf_path}")
        except Exception as e:
            print(f"[ERROR] Exception during profiling {pdf_path}: {e}")

    # Phase 2: Extraction
    try:
        with open("rubric/extraction_rules.yaml", "r") as f:
            rules = yaml.safe_load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load extraction rules: {e}")
        return

    router = ExtractionRouter(rules)
    profiles_dir = ".refinery/profiles"
    if not os.path.exists(profiles_dir):
        print(f"[ERROR] Profiles directory not found: {profiles_dir}")
        return

    profile_files = [f for f in os.listdir(profiles_dir) if f.endswith(".json")]
    if not profile_files:
        print(f"[ERROR] No profiles found in {profiles_dir}. Run profiling first.")
        return

    chunker = ChunkingEngine()
    indexer = PageIndexBuilder()
    for profile_file in profile_files:
        try:
            profile_path = os.path.join(profiles_dir, profile_file)
            with open(profile_path, "r") as f:
                profile_data = json.load(f)
            doc_id = str(profile_data.get("doc_id"))
            # Prefer original_pdf if present
            orig_pdf = profile_data.get("original_pdf")
            if orig_pdf and os.path.exists(os.path.join(args.dir, orig_pdf)):
                pdf_path = os.path.join(args.dir, orig_pdf)
            else:
                # Fallback: try doc_id.pdf
                pdf_path = os.path.join(args.dir, doc_id + ".pdf")
                if not os.path.exists(pdf_path):
                    print(f"[WARN] PDF not found for profile {profile_file} (tried {pdf_path})")
                    continue
            print(f"[INFO] Extracting: {pdf_path}")
            result = router.extract(pdf_path, profile_data, doc_id=doc_id)
            print(f"[RESULT] Extraction for {pdf_path}: {result}")
            # --- Semantic Chunking ---
            from src.models.models import ExtractedDocument
            extracted_doc = None
            def normalize_bbox(bbox):
                if isinstance(bbox, dict):
                    return bbox
                elif isinstance(bbox, list) and len(bbox) == 4:
                    return {"x0": bbox[0], "y0": bbox[1], "x1": bbox[2], "y1": bbox[3], "page": 1}
                else:
                    return {"x0": 0, "y0": 0, "x1": 0, "y1": 0, "page": 1}

            def normalize_blocks(blocks):
                for block in blocks:
                    if "bounding_box" in block:
                        block["bounding_box"] = normalize_bbox(block["bounding_box"])
                return blocks

            def normalize_tables(tables):
                for table in tables:
                    if "bbox" in table:
                        table["bbox"] = normalize_bbox(table["bbox"])
                    if "rows" in table:
                        for row in table["rows"]:
                            for cell in row:
                                if "bbox" in cell:
                                    cell["bbox"] = normalize_bbox(cell["bbox"])
                return tables

            def normalize_figures(figures):
                for fig in figures:
                    if "bbox" in fig:
                        fig["bbox"] = normalize_bbox(fig["bbox"])
                return figures

            if isinstance(result, dict) and "extracted_document" in result:
                doc = result["extracted_document"]
                if "text_blocks" in doc:
                    doc["text_blocks"] = normalize_blocks(doc["text_blocks"])
                if "tables" in doc:
                    doc["tables"] = normalize_tables(doc["tables"])
                if "figures" in doc:
                    doc["figures"] = normalize_figures(doc["figures"])
                try:
                    extracted_doc = ExtractedDocument(**doc)
                except Exception as e:
                    print(f"[ERROR] Could not parse ExtractedDocument for {pdf_path}: {e}")
                    traceback.print_exc()
            if extracted_doc:
                try:
                    ldu_list = chunker.chunk(extracted_doc)
                    print(f"[INFO] Chunked {len(ldu_list)} LDUs for {pdf_path}")
                    # Save LDUs to .refinery/ldus_<doc_id>.json
                    ldu_out_path = f".refinery/ldus_{doc_id}.json"
                    with open(ldu_out_path, "w") as f:
                        json.dump([ldu.model_dump() for ldu in ldu_list], f, indent=2)
                    print(f"[DEBUG] Wrote LDUs to {ldu_out_path}")
                except Exception as e:
                    print(f"[ERROR] Exception during chunking for {pdf_path}: {e}")
                    traceback.print_exc()
                # --- PageIndex Building ---
                try:
                    page_index = indexer.build(ldu_list)
                    print(f"[INFO] Built PageIndex for {pdf_path} with {len(page_index.child_sections)} sections.")
                    # Save PageIndex to .refinery/pageindex_<doc_id>.json
                    pageindex_out_path = f".refinery/pageindex_{doc_id}.json"
                    with open(pageindex_out_path, "w") as f:
                        json.dump(page_index.model_dump(), f, indent=2)
                    print(f"[DEBUG] Wrote PageIndex to {pageindex_out_path}")
                except Exception as e:
                    print(f"[ERROR] Exception during PageIndex building for {pdf_path}: {e}")
                    traceback.print_exc()
        except Exception as e:
            print(f"[ERROR] Exception during extraction for profile {profile_file}: {e}")
            print(f"[ERROR] Traceback for {profile_file}:")
            traceback.print_exc()

    print("[INFO] Extraction complete. See .refinery/extraction_ledger.jsonl for audit logs.")

if __name__ == "__main__":
    main()
