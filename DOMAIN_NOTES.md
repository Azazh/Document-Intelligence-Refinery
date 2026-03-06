# Phase 0: Domain Onboarding Findings

## PDF Analysis Summary (pdfplumber & Docling)

### Metrics Measured
- **Character Density:** Number of characters per page area. Indicates presence of extractable text.
- **Whitespace Ratio:** Proportion of page area not covered by text. High values suggest image-based or sparse documents.
- **BBox Variance:** Variance in character bounding box positions. Higher values indicate more distributed text layout.
- **Image to Page Ratio:** (Not available in this run; would indicate how much of the page is covered by images.)

### Results (Sample PDFs)
#### digital_CBE Annual Report 2012-13.pdf (Digital)
- Pages: 20
- Char Density (mean): 0.0024
- Whitespace Ratio (mean): 0.8392
- BBox Variance (mean): 17420.47
- **Docling:** No tables detected

#### scanned_2013-E.C-Audit-finding-information.pdf (Scanned)
- Pages: 3
- Char Density (mean): 0.0000
- Whitespace Ratio (mean): 1.0000
- BBox Variance (mean): 0.00
- **Docling:** No tables detected

#### mixed_CBE Annual Report 2017-18.pdf (Mixed)
- Pages: 171
- Char Density (mean): 0.0041
- Whitespace Ratio (mean): 0.7885
- BBox Variance (mean): 22838.18

### Interpretation & What the Output Indicates
- **Digital PDF:**
	- Nonzero character density and high bbox variance confirm presence of extractable text and distributed layout.
	- High whitespace ratio (>0.8) suggests significant non-text area (e.g., margins, images, or sparse layout).
	- Docling did not detect tables, indicating either absence of tables or limitations in table detection for this file.
- **Scanned PDF:**
	- Character density is exactly zero, whitespace ratio is 1.0, and bbox variance is 0.0. This means there is no extractable text—only images are present.
	- Both pdfplumber and Docling fail to extract tables or text, confirming that OCR or vision-based extraction is required for such files.
- **Mixed PDF:**
	- Low but nonzero character density, high bbox variance, and high whitespace ratio suggest a mix of extractable and non-extractable content, likely due to a combination of digital and scanned pages.

### Tool Comparison & Suitability
- **pdfplumber:**
	- Works well for digital PDFs with extractable text (nonzero char density).
	- Fails completely on scanned/image-based PDFs (char density = 0).
	- Provides useful layout metrics (char density, whitespace, bbox variance) for triage and classification.
- **Docling:**
	- Can process both digital and scanned PDFs, but in this run, did not detect any tables in either sample.
	- Table detection may be limited by document structure or tool capability; further testing with more table-rich documents is recommended.

### Failure Modes Observed
- **pdfplumber:**
	- Fails on scanned/image-based PDFs (no text extracted, all metrics zero except whitespace).
	- May miss tables if they are not represented as extractable text.
- **Docling:**
	- Did not detect tables in either digital or scanned sample, possibly due to document structure or tool limitations.
	- No errors, but output is empty for table extraction in these samples.

### Conclusions & Recommendations
- Use **pdfplumber** for digital PDFs where character density is nonzero; it provides reliable text and layout features for triage and extraction.
- For scanned/image-based PDFs (char density ≈ 0, whitespace ≈ 1), escalate to OCR or vision-based extraction, as both pdfplumber and Docling will fail to extract meaningful content.
- Table detection with Docling may require further tuning or alternative tools for documents with complex or nonstandard table layouts.
- Always measure character density and whitespace ratio as first-pass triage features to select the appropriate extraction strategy.
