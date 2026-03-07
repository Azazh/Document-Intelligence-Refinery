from typing import List, Optional, Dict, Any, Literal, Union
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, model_validator

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
    """
    Represents a bounding box on a page.
    Invariants:
        - x1 >= x0, y1 >= y0
        - page >= 1
    """
    x0: float
    y0: float
    x1: float
    y1: float
    page: int

    @field_validator('x1')
    @classmethod
    def check_x1_positive(cls, v, info):
        x0 = info.data.get('x0')
        if x0 is not None and v < x0:
            raise ValueError('x1 must be >= x0')
        return v

    @field_validator('y1')
    @classmethod
    def check_y1_positive(cls, v, info):
        y0 = info.data.get('y0')
        if y0 is not None and v < y0:
            raise ValueError('y1 must be >= y0')
        return v

    @field_validator('page')
    @classmethod
    def check_page_positive(cls, v):
        if v < 1:
            raise ValueError('page must be >= 1')
        return v

# --- ProvenanceChain ---
class ProvenanceChain(BaseModel):
    document_name: str
    page_number: int
    bounding_box: BoundingBox
    content_hash: str

# --- LDU (Logical Document Unit) ---
class LDU(BaseModel):
    """
    Logical Document Unit (LDU).
    Invariants:
        - content must be non-empty
        - page_refs must be non-empty and all >= 1
        - token_count > 0
    """
    ldu_id: str
    content: str
    chunk_type: Literal['text', 'table', 'figure', 'list', 'header', 'other']
    page_refs: List[int]
    bounding_box: Optional[BoundingBox]
    parent_section: Optional[str]
    token_count: int
    content_hash: str
    metadata: Optional[Dict[str, Any]] = None
    document_name: Optional[str] = None  # Name of the source document

    @field_validator('content')
    @classmethod
    def content_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('LDU content must be non-empty')
        return v

    @field_validator('page_refs')
    @classmethod
    def page_refs_not_empty(cls, v):
        if not v:
            raise ValueError('LDU must have at least one page_ref')
        if any(page < 1 for page in v):
            raise ValueError('All page_refs must be >= 1')
        return v

    @field_validator('token_count')
    @classmethod
    def token_count_positive(cls, v):
        if v < 1:
            raise ValueError('token_count must be positive')
        return v

# --- TableCell ---
class TableCell(BaseModel):
    """
    Represents a cell in a table.
    Invariants:
        - row, col >= 0
    """
    text: str
    bbox: BoundingBox
    row: int
    col: int

# --- TableBlock ---
class TableBlock(BaseModel):
    """
    Represents a table block with headers and rows.
    """
    headers: List[str]
    rows: List[List[TableCell]]
    bbox: BoundingBox

# --- FigureBlock ---
class FigureBlock(BaseModel):
    """
    Represents a figure block with caption and bounding box.
    """
    caption: str
    bbox: BoundingBox
    page: int

# --- ExtractedDocument ---
class ExtractedDocument(BaseModel):
    """
    Represents the full extracted content of a document.
    """
    doc_id: UUID
    text_blocks: List[LDU]
    tables: List[TableBlock]
    figures: List[FigureBlock]
    reading_order: List[str]  # List of LDU IDs in reading order

# --- PageIndex Section Node ---
class PageIndexSection(BaseModel):
    """
    Represents a section in the page index hierarchy.
    Invariants:
        - page_end >= page_start
        - child_sections must not overlap in page ranges
    """
    section_id: str
    title: str
    page_start: int
    page_end: int
    child_sections: List['PageIndexSection'] = []
    key_entities: List[str] = []
    summary: Optional[str] = None
    data_types_present: List[str] = []  # e.g., ['table', 'figure']
    ldu_ids: List[str] = []  # List of LDU IDs belonging to this section

    @field_validator('page_end')
    @classmethod
    def page_range_valid(cls, v, info):
        page_start = info.data.get('page_start')
        if page_start is not None and v < page_start:
            raise ValueError('page_end must be >= page_start')
        return v

    @model_validator(mode="after")
    def check_no_overlap(self):
        children = self.child_sections or []
        ranges = [(c.page_start, c.page_end) for c in children]
        for i, (s1, e1) in enumerate(ranges):
            for j, (s2, e2) in enumerate(ranges):
                if i != j and not (e1 < s2 or e2 < s1):
                    raise ValueError('Child sections must not overlap')
        return self

    class Config:
        arbitrary_types_allowed = True

# --- PageIndex ---
class PageIndex(BaseModel):
    doc_id: UUID
    root_section: PageIndexSection

# For recursive models
PageIndexSection.update_forward_refs()
