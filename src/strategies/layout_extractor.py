from src.models.models import TableBlock, TableCell, BoundingBox
"""
LayoutExtractor: Production-grade layout-aware extraction for complex PDFs.

Implements a layout-aware extraction strategy using pdfplumber and clustering heuristics, following industry best practices:
- Detects multi-column, table-heavy, and figure-heavy layouts
- Extracts text blocks with bounding boxes, tables as structured JSON, and figures with captions
- Modular, clean, and extensible for real-world pipelines

Usage:
    extractor = LayoutExtractor(rules)
    result, confidence = extractor.extract(pdf_path)
"""
import pdfplumber
from typing import Dict, Any, Tuple
import os
import numpy as np
from sklearn.cluster import KMeans
from src.strategies.base_extractor import BaseExtractor
from uuid import uuid4

class LayoutExtractor(BaseExtractor):
    def _normalize_bbox(self, bbox, page_num):
        if isinstance(bbox, dict):
            return {
                'x0': bbox.get('x0', 0),
                'y0': bbox.get('y0', 0),
                'x1': bbox.get('x1', 0),
                'y1': bbox.get('y1', 0),
                'page': bbox.get('page', page_num)
            }
        elif isinstance(bbox, list) and len(bbox) == 4:
            return {
                'x0': bbox[0],
                'y0': bbox[1],
                'x1': bbox[2],
                'y1': bbox[3],
                'page': page_num
            }
        else:
            return {'x0': 0, 'y0': 0, 'x1': 0, 'y1': 0, 'page': page_num}

    def _normalize_table(self, table_dict, page_num):
        bbox = self._normalize_bbox(table_dict.get('bbox', [0, 0, 0, 0]), page_num)
        # Ensure all headers are strings and not None
        headers = [str(h) if h is not None else "" for h in table_dict.get('headers', [])]
        norm_rows = []
        for r_idx, row in enumerate(table_dict.get('rows', [])):
            norm_row = []
            for c_idx, cell in enumerate(row):
                if isinstance(cell, dict):
                    text = cell.get('text', str(cell))
                    cell_bbox = self._normalize_bbox(cell.get('bbox', bbox), page_num)
                else:
                    text = str(cell)
                    cell_bbox = bbox
                norm_row.append({
                    'text': text,
                    'bbox': cell_bbox,
                    'row': r_idx,
                    'col': c_idx
                })
            norm_rows.append(norm_row)
        return {
            'headers': headers,
            'rows': norm_rows,
            'bbox': bbox
        }

    def extract(self, pdf_path: str) -> Tuple[Dict[str, Any], float]:
        """
        Multi-signal confidence scoring:
            - Multi-column detection (clustering)
            - Block count (extraction quality)
        Table and figure structures are preserved and normalized.
        Extracts layout-aware content from a PDF using pdfplumber and clustering.
        Returns structured text blocks, tables, and figures with bounding boxes.
        Computes a confidence score based on layout detection and extraction quality.
        All thresholds and weights are loaded from config.
        Output is normalized to ExtractedDocument/LDU schema.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        with pdfplumber.open(pdf_path) as pdf:
            ldu_list = []
            table_list = []
            figure_list = []
            total_blocks = 0
            multi_column_pages = 0
            for i, page in enumerate(pdf.pages):
                blocks = []
                # Extract text blocks with bounding boxes
                for b in page.extract_words(x_tolerance=2, y_tolerance=2):
                    blocks.append({
                        "text": b["text"],
                        "bbox": [b["x0"], b["top"], b["x1"], b["bottom"]],
                    })
                total_blocks += len(blocks)
                # Detect multi-column layout using clustering on x0 positions
                if len(blocks) > 10:
                    x0s = np.array([[b["bbox"][0]] for b in blocks])
                    kmeans = KMeans(n_clusters=2, n_init=10, random_state=42).fit(x0s)
                    if np.abs(kmeans.cluster_centers_[0][0] - kmeans.cluster_centers_[1][0]) > 100:
                        multi_column_pages += 1
                # Normalize to LDU
                for block in blocks:
                    ldu_list.append({
                        "ldu_id": str(uuid4()),
                        "content": block["text"],
                        "chunk_type": "text",
                        "page_refs": [i+1],
                        "bounding_box": self._normalize_bbox(block["bbox"], i+1),
                        "parent_section": None,
                        "token_count": len(block["text"].split()),
                        "content_hash": str(hash(block["text"])),
                        "metadata": {"block_type": "layout"}
                    })
                # Extract tables (preserve structure)
                tables = page.extract_tables() or []
                for t in tables:
                    table_dict = {
                        "headers": t[0] if t else [],
                        "rows": t[1:] if len(t) > 1 else [],
                        "bbox": [0, 0, page.width, page.height]
                    }
                    norm_table = self._normalize_table(table_dict, page_num=i+1)
                    table_list.append(norm_table)
                # Extract figures (preserve structure)
                figures = page.images or []
                for f in figures:
                    figure_list.append({
                        "caption": f.get("caption", ""),
                        "bbox": self._normalize_bbox([f.get("x0", 0), f.get("top", 0), f.get("x1", 0), f.get("bottom", 0)], i+1),
                        "page": i+1
                    })
            # Multi-signal confidence scoring
            # Defensive: ensure self.rules is a dict and weights is always a dict
            rules = self.rules if isinstance(self.rules, dict) else {}
            weights = rules.get("confidence_weights")
            if not isinstance(weights, dict):
                weights = {}
            conf = 1.0
            if multi_column_pages > 0:
                conf *= 1 - weights.get("char_density", 0.3)  # Penalize if multi-column detected
            if total_blocks < 10 * len(pdf.pages):
                conf *= 0.7
            result = {
                "extracted_document": {
                    "doc_id": str(uuid4()),
                    "text_blocks": ldu_list,
                    "tables": table_list,
                    "figures": figure_list,
                    "reading_order": [ldu["ldu_id"] for ldu in ldu_list]
                },
                "multi_column_pages": multi_column_pages,
                "total_blocks": total_blocks
            }
            return result, conf
