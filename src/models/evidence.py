from typing import List, Optional
from pydantic import BaseModel

class BoundingBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float

class Evidence(BaseModel):
    document_id: str
    document_name: str
    page_number: int
    text_snippet: str
    table_index: Optional[int] = None
    row_index: Optional[int] = None
    column_index: Optional[int] = None
    bounding_box: Optional[BoundingBox] = None
    surrounding_context: Optional[str] = None
    source_type: str = 'text'  # 'table', 'text', 'footnote', 'header'
