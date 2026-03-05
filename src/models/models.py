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

    @validator('x1', 'y1')
    def check_bbox_positive(cls, v, values, field):
        if field.name == 'x1' and 'x0' in values and v < values['x0']:
            raise ValueError('x1 must be >= x0')
        if field.name == 'y1' and 'y0' in values and v < values['y0']:
            raise ValueError('y1 must be >= y0')
        return v
    @validator('page')
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
    ldu_id: str
    content: str
    chunk_type: Literal['text', 'table', 'figure', 'list', 'header', 'other']
    page_refs: List[int]
    bounding_box: Optional[BoundingBox]
    parent_section: Optional[str]
    token_count: int
    content_hash: str
    metadata: Optional[Dict[str, Any]] = None

    @validator('content')
    def content_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('LDU content must be non-empty')
        return v
    @validator('page_refs')
    def page_refs_not_empty(cls, v):
        if not v:
            raise ValueError('LDU must have at least one page_ref')
        if any(page < 1 for page in v):
            raise ValueError('All page_refs must be >= 1')
        return v
    @validator('token_count')
    def token_count_positive(cls, v):
        if v < 1:
            raise ValueError('token_count must be positive')
        return v

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

    @validator('page_end')
    def page_range_valid(cls, v, values):
        if 'page_start' in values and v < values['page_start']:
            raise ValueError('page_end must be >= page_start')
        return v

    @root_validator
    def check_no_overlap(cls, values):
        children = values.get('child_sections', [])
        ranges = [(c.page_start, c.page_end) for c in children]
        for i, (s1, e1) in enumerate(ranges):
            for j, (s2, e2) in enumerate(ranges):
                if i != j and not (e1 < s2 or e2 < s1):
                    raise ValueError('Child sections must not overlap')
        return values

    class Config:
        arbitrary_types_allowed = True

# --- PageIndex ---
class PageIndex(BaseModel):
    doc_id: UUID
    root_section: PageIndexSection

# For recursive models
PageIndexSection.update_forward_refs()
