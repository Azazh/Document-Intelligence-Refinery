### Comparison: `pdfplumber` vs. Docling
**PDF:** `scanned_2013-E.C-Audit-finding-information.pdf`
**Type:** Scanned (image-based, no text layer)

| **Metric**               | **pdfplumber**                          | **Docling**                                | **Winner**       |
|--------------------------|-----------------------------------------|--------------------------------------------|-------------------|
| **Pages Processed**      | 3                                       | 3                                          | Tie               |
| **Char Density (mean)**  | 0.0                                     | N/A (Docling does not report)              | Tie               |
| **Whitespace Ratio**     | 1.0                                     | N/A (Docling does not report)              | Tie               |
| **Bbox Variance**        | 0.0                                     | N/A (Docling does not report)              | Tie               |
| **Table Quality**        | ❌ No tables detected                   | ❌ No tables detected                      | Tie               |
| **Figure Handling**      | ❌ Not detected                         | ❌ Not detected                            | Tie               |
| **Layout Preservation**  | ❌ Not applicable (no text)             | ❌ Not applicable (no text)                | Tie               |
| **Processing Time**      | Fast                                    | Moderate                                   | pdfplumber        |
| **Output Usability**     | No text extracted                       | Minimal structure, no text                 | Tie               |

---

### **Detailed Observations**
1. **Text Extraction:**
   - `pdfplumber` failed to extract any text (char density = 0, whitespace = 1.0), confirming the document is scanned.
   - Docling produced a valid JSON structure but did not extract any meaningful text or tables.

2. **Tables and Figures:**
   - Neither tool detected tables or figures in this document.

3. **Layout Preservation:**
   - Not applicable, as no text was extracted by either tool.

4. **Performance:**
   - `pdfplumber` is faster, but both tools provide minimal output for scanned PDFs.

5. **Output Usability:**
   - Both outputs are of limited use for downstream processing; OCR or a vision model is needed for this type.

---

### **Conclusion for This PDF**
**Use Case:** Scanned PDF (image-based, no text layer).

| **Tool**       | **When to Use**                                                                 | **When to Avoid**                          |
|----------------|---------------------------------------------------------------------------------|--------------------------------------------|
| **pdfplumber** | - Digital PDFs with a text layer.                                             | Scanned/image-based PDFs.                  |
| **Docling**    | - Digital PDFs with complex layout.                                            | Scanned/image-based PDFs.                  |
| **VLM**        | - Scanned PDFs or handwritten text.                                            | Digital PDFs (overkill).                  |

**Recommendation for This PDF:**
- **Neither pdfplumber nor Docling** is suitable for scanned PDFs. Use a vision model (VLM/OCR) for extraction.

---
