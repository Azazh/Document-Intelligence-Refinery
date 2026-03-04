"""
Modular Phase 0 Analysis: pdfplumber for all sample PDFs, Docling for digital and scanned only.
- pdfplumber: character density, bbox variance, whitespace ratio
- Docling: table extraction summary (digital + scanned only)
"""
import os
import json
import subprocess
import numpy as np
import pdfplumber


SAMPLE_DIR = "./sample"
OUTPUT_DIR = "./sample/analysis_outputs"
# Overwrite output folder on every run
import shutil
if os.path.exists(OUTPUT_DIR):
    shutil.rmtree(OUTPUT_DIR)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# Dynamically detect the current digital and scanned sample files in the sample directory
def get_sample_file(prefix):
    for f in os.listdir(SAMPLE_DIR):
        if f.lower().endswith('.pdf') and f.startswith(prefix + "_"):
            return f
    return None

def analyze_pdfplumber(pdf_path):
    results = {
        "file": os.path.basename(pdf_path),
        "character_density": [],
        "whitespace_ratio": [],
        "bbox_variance": [],
        "page_count": 0,
    }
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                area = page.width * page.height
                chars = page.chars
                char_count = len(chars)
                char_density = char_count / area if area > 0 else 0
                results["character_density"].append(char_density)
                char_bboxes = [(
                    float(c["x0"]), float(c["top"]), float(c["x1"]), float(c["bottom"])
                ) for c in chars]
                if char_bboxes:
                    char_area = sum((x1-x0)*(b-y) for x0,y,x1,b in char_bboxes)
                    whitespace = 1 - (char_area / area)
                else:
                    whitespace = 1.0
                results["whitespace_ratio"].append(whitespace)
                if char_bboxes:
                    x0s = [x0 for x0,_,_,_ in char_bboxes]
                    x1s = [x1 for _,_,x1,_ in char_bboxes]
                    bbox_var = np.var(x0s + x1s)
                else:
                    bbox_var = 0.0
                results["bbox_variance"].append(bbox_var)
            results["page_count"] = len(pdf.pages)
    except Exception as e:
        results["error"] = str(e)
    return results

def run_docling(pdf_path):
    abs_pdf = os.path.abspath(pdf_path)
    out_dir = OUTPUT_DIR
    base = os.path.splitext(os.path.basename(pdf_path))[0]
    result = subprocess.run([
        "docling", "--to", "json", "--output", out_dir, abs_pdf
    ], capture_output=True, text=True, timeout=300)
    out_json = os.path.join(out_dir, base + ".json")
    if result.returncode != 0:
        return None, f"Docling failed: {result.stderr.strip()}"
    if not os.path.exists(out_json):
        return None, f"Docling did not produce expected output: {out_json}"
    try:
        with open(out_json, "r") as f:
            doc = json.load(f)
        tables = [b for b in doc.get("blocks", []) if b.get("type") == "table"]
        if not tables:
            summary = "No tables detected"
        else:
            preserved = sum(1 for t in tables if t.get("header"))
            summary = f"{preserved}/{len(tables)} tables with headers preserved"
        return doc, summary
    except Exception as e:
        return None, f"Error reading Docling output: {e}"

def main():
    pdfs = [os.path.join(SAMPLE_DIR, f) for f in os.listdir(SAMPLE_DIR) if f.lower().endswith(".pdf")]
    # Detect current digital and scanned sample files (skip mixed for Docling)
    digital_pdf = get_sample_file("digital")
    scanned_pdf = get_sample_file("scanned")
    docling_targets = [(digital_pdf, "digital"), (scanned_pdf, "scanned")]  # skip mixed
    plumber_results = []
    print("\n=== PDFPlumber Analysis (All Sample PDFs) ===")
    for pdf in pdfs:
        res = analyze_pdfplumber(pdf)
        plumber_results.append(res)
        print(f"\nFile: {res['file']}")
        print(f"  Pages: {res['page_count']}")
        print(f"  Char Density (mean): {np.mean(res['character_density']):.4f}")
        print(f"  Whitespace Ratio (mean): {np.mean(res['whitespace_ratio']):.4f}")
        print(f"  Bbox Variance (mean): {np.mean(res['bbox_variance']):.2f}")
        if 'error' in res:
            print(f"  Error: {res['error']}")
    # Write all pdfplumber results to a single JSON file
    plumber_json = os.path.join(OUTPUT_DIR, "pdfplumber_results.json")
    with open(plumber_json, "w") as f:
        json.dump(plumber_results, f, indent=2)
    print(f"\nPDFPlumber results exported to {plumber_json}")

    # Run Docling only on digital and scanned sample PDFs and aggregate outputs
    print("\n=== Docling Full Output (Digital & Scanned Only) ===")
    docling_results = []
    for fname, pdf_type in docling_targets:
        if not fname:
            print(f"\nNo sample file found for type: {pdf_type}")
            docling_results.append({
                "file": None,
                "pdf_type": pdf_type,
                "docling_output": None,
                "table_summary": "No sample file found"
            })
            continue
        pdf_path = os.path.join(SAMPLE_DIR, fname)
        doc, summary = run_docling(pdf_path)
        docling_results.append({
            "file": fname,
            "pdf_type": pdf_type,
            "docling_output": doc,
            "table_summary": summary
        })
        print(f"\nDocling on: {fname} ({pdf_type})")
        print(f"  Table Extraction Summary: {summary}")
    docling_json = os.path.join(OUTPUT_DIR, "docling_full_results.json")
    with open(docling_json, "w") as f:
        json.dump(docling_results, f, indent=2)
    print(f"\nDocling results exported to {docling_json}")
    # Merge pdfplumber and docling results into a single file for convenience
    merged_results = {
        "pdfplumber": plumber_results,
        "docling": docling_results
    }
    merged_json = os.path.join(OUTPUT_DIR, "merged_results.json")
    with open(merged_json, "w") as f:
        json.dump(merged_results, f, indent=2)
    print(f"\nMerged results exported to {merged_json}")

    # Quality comparison for digital and scanned only
    docling_comparison = []
    for fname, pdf_type in docling_targets:
        if not fname:
            print(f"\nNo sample file found for type: {pdf_type}")
            docling_comparison.append({
                "file": None,
                "pdf_type": pdf_type,
                "pdfplumber": None,
                "docling_table_summary": "No sample file found"
            })
            continue
        pdf_path = os.path.join(SAMPLE_DIR, fname)
        # Find docling result for this file
        docling_res = next((r for r in docling_results if r['file'] == fname), None)
        summary = docling_res['table_summary'] if docling_res else "No result"
        # Find corresponding pdfplumber result
        plumber_res = next((r for r in plumber_results if r['file'] == fname), None)
        docling_comparison.append({
            "file": fname,
            "pdf_type": pdf_type,
            "pdfplumber": plumber_res,
            "docling_table_summary": summary
        })
    # Print and export comparison summary for all types
    comparison_json = os.path.join(OUTPUT_DIR, "quality_comparison_report.json")
    print("\n=== Quality Comparison Report (Digital & Scanned) ===")
    for comp in docling_comparison:
        print(f"\nPDF Type: {comp['pdf_type']}")
        if comp['file']:
            print(f"  File: {comp['file']}")
        p = comp['pdfplumber']
        if p:
            print(f"  PDFPlumber: Pages={p['page_count']}, CharDensity={np.mean(p['character_density']):.4f}, Whitespace={np.mean(p['whitespace_ratio']):.4f}, BboxVar={np.mean(p['bbox_variance']):.2f}")
        else:
            print("  PDFPlumber: No result found.")
        print(f"  Docling: {comp['docling_table_summary']}")
    with open(comparison_json, "w") as f:
        json.dump(docling_comparison, f, indent=2)
    print(f"\nQuality comparison report exported to {comparison_json}")

if __name__ == "__main__":
    main()
