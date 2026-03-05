from typing import List, Optional, Dict, Any, Literal, Union
from uuid import UUID
from pydantic import BaseModel, Field

# --- DocumentProfile (already present, shown for completeness) ---
class DocumentProfile(BaseModel):
    doc_id: UUID
    origin_type: Literal['native_digital', 'scanned_image', 'mixed', 'form_fillable']
    layout_complexity: Literal['single_column', 'multi_column', 'table_heavy', 'figure_heavy', 'mixed']
    language: str  # ISO code
    domain_hint: Literal['financial', 'legal', 'technical', 'medical', 'general']
    extraction_metrics: Dict[str, float] = Field(
        ..., description="Metrics such as character_density, whitespace_ratio, image_to_page_ratio"
    )
    estimated_cost_tier: Literal['low', 'medium', 'high']

# --- BoundingBox ---
class BoundingBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float
    page: int

# --- ProvenanceChain ---
class ProvenanceChain(BaseModel):
    document_name: str
    page_number: int
    bounding_box: BoundingBox
    content_hash: str

# --- LDU (Logical Document Unit) ---
class LDU(BaseModel):
    ldu_id: str
    content: str
    chunk_type: Literal['text', 'table', 'figure', 'list', 'header', 'other']
    page_refs: List[int]
    bounding_box: Optional[BoundingBox]
    parent_section: Optional[str]
    token_count: int
    content_hash: str
    metadata: Optional[Dict[str, Any]] = None

# --- TableCell ---
class TableCell(BaseModel):
    text: str
    bbox: BoundingBox
    row: int
    col: int

# --- TableBlock ---
class TableBlock(BaseModel):
    headers: List[str]
    rows: List[List[TableCell]]
    bbox: BoundingBox

# --- FigureBlock ---
class FigureBlock(BaseModel):
    caption: str
    bbox: BoundingBox
    page: int

# --- ExtractedDocument ---
class ExtractedDocument(BaseModel):
    doc_id: UUID
    text_blocks: List[LDU]
    tables: List[TableBlock]
    figures: List[FigureBlock]
    reading_order: List[str]  # List of LDU IDs in reading order

# --- PageIndex Section Node ---
class PageIndexSection(BaseModel):
    section_id: str
    title: str
    page_start: int
    page_end: int
    child_sections: List['PageIndexSection'] = []
    key_entities: List[str] = []
    summary: Optional[str] = None
    data_types_present: List[str] = []  # e.g., ['table', 'figure']

    class Config:
        arbitrary_types_allowed = True

# --- PageIndex ---
class PageIndex(BaseModel):
    doc_id: UUID
    root_section: PageIndexSection

# For recursive models
PageIndexSection.update_forward_refs()
