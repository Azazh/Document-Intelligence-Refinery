from typing import Dict, Literal
from uuid import UUID
from pydantic import BaseModel, Field

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
