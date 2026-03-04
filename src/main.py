import os
import argparse
from src.agents.triage import TriageAgent

def main():
    sample_dir = "./sample"
    parser = argparse.ArgumentParser(description="Run TriageAgent on sample PDFs.")
    parser.add_argument(
        "--dir", type=str, default=sample_dir,
        help="Directory containing PDF files to process (default: ./sample)"
    )
    args = parser.parse_args()

    agent = TriageAgent()
    pdf_files = [
        os.path.join(args.dir, f)
        for f in os.listdir(args.dir)
        if f.lower().endswith(".pdf")
    ]
    print(f"[DEBUG] Found {len(pdf_files)} PDF(s) in {args.dir}")
    if not pdf_files:
        print(f"No PDF files found in {args.dir}")
    for pdf_path in pdf_files:
        print(f"[DEBUG] Processing: {pdf_path}")
        profile = agent.analyze_pdf(pdf_path)
        if profile:
            print(f"[DEBUG] Profile saved for {pdf_path} (doc_id={profile.doc_id})")
        else:
            print(f"[ERROR] Failed to process {pdf_path}")

if __name__ == "__main__":
    main()
