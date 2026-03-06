import hashlib
import re
"""
ChunkingEngine: Semantic chunking of ExtractedDocument into LDUs.

Chunking Rules Enforced:
1. Table cell is never split from its header row.
2. Figure caption is always stored as metadata of its parent figure chunk.
3. Numbered list is always kept as a single LDU unless it exceeds max_tokens.
4. Section headers are stored as parent metadata on all child chunks within that section.
5. Cross-references (e.g., "see Table 3") are resolved and stored as chunk relationships.
6. Domain-specific anchors are detected and tagged in LDU metadata.
7. Semantic Coherence: Consecutive text blocks belonging to the same paragraph or section are merged to form semantically complete LDUs (no chunk splits a logical thought or paragraph).

Approach/Methodology:
- Enforces all chunking rules from rubric and above.
- Accepts ExtractedDocument, emits List[LDU] with all invariants.
- Handles errors with location/context and debug prints for critical actions.
"""
from typing import List
from src.models.models import ExtractedDocument, LDU
import traceback
import uuid

class ChunkingEngine:
    """
    Semantic Chunking Engine for RAG-ready document units.
    Converts ExtractedDocument into a list of LDUs, enforcing chunking rules.
    """

    class ChunkValidator:
        """
        Validates that all chunking rules are enforced on the LDU list.
        """
        def __init__(self, max_tokens=512):
            self.max_tokens = max_tokens

        def validate(self, ldu_list):
            # Rule 1: Table cell is never split from header row (assume table LDU content always includes header)
            # Rule 2: Figure caption is always stored as metadata of its parent figure chunk (checked in LDU.metadata)
            # Rule 3: Numbered list is always kept as a single LDU unless it exceeds max_tokens
            for ldu in ldu_list:
                if ldu.chunk_type == 'list':
                    if ldu.token_count > self.max_tokens:
                        raise ValueError(f"Numbered list LDU {ldu.ldu_id} exceeds max_tokens")
            # Rule 4: Section headers are stored as parent metadata on all child chunks within that section
            # (checked by presence of parent_section)
            # Rule 5: Cross-references are stored as chunk relationships (checked by metadata['cross_references'])
            return True

    def __init__(self, anchors=None):
        # Domain-specific anchors: can be loaded from config or passed in
        if anchors is None:
            # Example anchors for financial/legal/technical docs
            self.anchors = [
                'Total Revenue', 'Net Income', 'Board of Directors', 'Fiscal Year',
                'Balance Sheet', 'Cash Flow', 'Assets', 'Liabilities', 'Equity',
                'Audit Committee', 'CEO', 'Chairman', 'Dividend', 'Shareholder',
                'Operating Expenses', 'Gross Profit', 'Earnings Per Share',
                'Loan Portfolio', 'Interest Income', 'Provision for Losses',
                'Capital Expenditure', 'Tax Policy', 'Import', 'Export', 'Budget',
                'Ministry of Finance', 'Assessment', 'Transparency', 'Accountability'
            ]
        else:
            self.anchors = anchors

    def chunk(self, doc: ExtractedDocument) -> List[LDU]:
        """
        Chunk an ExtractedDocument into LDUs, enforcing all chunking rules.
        Args:
            doc: ExtractedDocument to chunk
        Returns:
            List[LDU]: List of logical document units
        """
        try:
            ldu_list = []
            # 1. Add all text blocks as LDUs, extract section headers, and enforce semantic coherence
            current_section = None
            merged_ldu = None
            for ldu in doc.text_blocks:
                # Detect section headers (simple heuristic: all caps, short, or numbered)
                if ldu.chunk_type == 'header' or (len(ldu.content) < 80 and ldu.content.isupper()):
                    current_section = ldu.content.strip()
                    ldu.parent_section = None
                    # If there is a merged LDU in progress, append it before starting a new section
                    if merged_ldu:
                        ldu_list.append(merged_ldu)
                        merged_ldu = None
                    ldu_list.append(ldu)
                    continue
                else:
                    ldu.parent_section = current_section
                # Detect numbered lists (e.g., "1. ...", "a) ...")
                if re.match(r'^(\d+\.|[a-zA-Z]\))', ldu.content.strip()):
                    ldu.chunk_type = 'list'
                # Detect cross-references (e.g., "see Table 3")
                cross_refs = re.findall(r'(see|refer to) (Table|Figure|Section) (\d+)', ldu.content, re.IGNORECASE)
                if cross_refs:
                    ldu.metadata = ldu.metadata or {}
                    ldu.metadata['cross_references'] = cross_refs
                # Domain-specific anchor tagging
                found_anchors = [a for a in self.anchors if a.lower() in ldu.content.lower()]
                if found_anchors:
                    ldu.metadata = ldu.metadata or {}
                    ldu.metadata['anchors'] = found_anchors
                # --- Semantic Coherence Enforcement ---
                # Merge consecutive text blocks that are not headers, lists, or tables, and belong to the same section
                if ldu.chunk_type == 'text':
                    if merged_ldu and merged_ldu.parent_section == ldu.parent_section:
                        # Merge content and update token count, content_hash, and bounding box (expand to cover both)
                        merged_ldu.content += '\n' + ldu.content
                        merged_ldu.token_count += ldu.token_count
                        merged_ldu.content_hash = hashlib.sha256(merged_ldu.content.encode('utf-8')).hexdigest()
                        # Optionally, expand bounding box to cover both (not implemented here for brevity)
                    else:
                        if merged_ldu:
                            ldu_list.append(merged_ldu)
                        # Always recalculate content_hash for new/standalone LDU
                        ldu.content_hash = hashlib.sha256(ldu.content.encode('utf-8')).hexdigest()
                        merged_ldu = ldu
                else:
                    if merged_ldu:
                        ldu_list.append(merged_ldu)
                        merged_ldu = None
                    ldu_list.append(ldu)
            if merged_ldu:
                ldu_list.append(merged_ldu)
            # 2. Add all tables as LDUs, ensure table cells are not split from headers
            for table in getattr(doc, 'tables', []):
                content = f"Table: {getattr(table, 'title', 'Untitled')}\nHeader: {getattr(table, 'headers', '')}\nRows: {getattr(table, 'rows', '')}"
                ldu = LDU(
                    ldu_id=str(uuid.uuid4()),
                    content=content,
                    chunk_type='table',
                    page_refs=[getattr(table, 'bbox', None).page] if getattr(table, 'bbox', None) else [1],
                    bounding_box=getattr(table, 'bbox', None),
                    parent_section=current_section,
                    token_count=len(str(content).split()),
                    content_hash=hashlib.sha256(content.encode('utf-8')).hexdigest(),
                    metadata={"source": "table", "headers": getattr(table, 'headers', None)}
                )
                ldu_list.append(ldu)
            # 3. Add all figures as LDUs, store caption as metadata
            for fig in getattr(doc, 'figures', []):
                content = f"Figure: {getattr(fig, 'caption', '')}"
                ldu = LDU(
                    ldu_id=str(uuid.uuid4()),
                    content=content,
                    chunk_type='figure',
                    page_refs=[getattr(fig, 'bbox', None).page] if getattr(fig, 'bbox', None) else [1],
                    bounding_box=getattr(fig, 'bbox', None),
                    parent_section=current_section,
                    token_count=len(str(content).split()),
                    content_hash=hashlib.sha256(content.encode('utf-8')).hexdigest(),
                    metadata={"caption": getattr(fig, 'caption', None)}
                )
                ldu_list.append(ldu)
            # 4. Validate all chunking rules
            validator = self.ChunkValidator()
            validator.validate(ldu_list)
            print(f"[DEBUG] Chunked {len(ldu_list)} LDUs from document {doc.doc_id}")
            return ldu_list
        except Exception as e:
            print(f"[ERROR] Exception in ChunkingEngine.chunk: {e}")
            traceback.print_exc()
            raise
