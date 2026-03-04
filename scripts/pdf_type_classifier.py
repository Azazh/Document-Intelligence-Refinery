import os
import fitz  # PyMuPDF
from collections import defaultdict
import shutil

# Paths
DATA_DIR = "./data"
SAMPLE_DIR = "./sample"
SAMPLES_PER_TYPE = 1

# PDF type detection
# - 'digital': all pages have text layer, few or no images
# - 'scanned': all pages are images, no text layer
# - 'mixed': some pages have text, some are images

def detect_pdf_type(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text_pages = 0
        image_pages = 0
        for page in doc:
            text = page.get_text().strip()
            images = page.get_images(full=True)
            if text:
                text_pages += 1
            if images and not text:
                image_pages += 1
        if text_pages == len(doc) and image_pages == 0:
            return 'digital'
        elif image_pages == len(doc) and text_pages == 0:
            return 'scanned'
        elif text_pages > 0 and image_pages > 0:
            return 'mixed'
        else:
            return 'unknown'
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return 'error'

def main():
    pdf_types = defaultdict(list)
    for root, _, files in os.walk(DATA_DIR):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_path = os.path.join(root, file)
                pdf_type = detect_pdf_type(pdf_path)
                if pdf_type in ['digital', 'scanned', 'mixed']:
                    pdf_types[pdf_type].append(pdf_path)
                else:
                    print(f"Skipped {pdf_path} (type: {pdf_type})")

    # For each type, select the smallest file (by size) as the sample
    os.makedirs(SAMPLE_DIR, exist_ok=True)
    for pdf_type, paths in pdf_types.items():
        if not paths:
            continue
        # Sort by file size (ascending)
        smallest = min(paths, key=lambda p: os.path.getsize(p))
        original_filename = os.path.basename(smallest)
        dest_filename = f"{pdf_type}_{original_filename}"
        dest = os.path.join(SAMPLE_DIR, dest_filename)
        shutil.copy2(smallest, dest)
        print(f"Copied {smallest} -> {dest} (smallest {pdf_type})")

    # Summary
    for pdf_type in ['digital', 'scanned', 'mixed']:
        print(f"{pdf_type.title()} PDFs found: {len(pdf_types[pdf_type])}")

if __name__ == "__main__":
    main()