from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class BoundingBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float

class Evidence(BaseModel):
    evidence_id: str
    document_id: str
    document_name: str
    page_number: int
    bbox: Optional[List[float]] = None  # [x0, y0, x1, y1]
    text_snippet: str
    section_name: Optional[str] = None
    table_context: Optional[Dict[str, Any]] = None
    extraction_method: str = "pdf_layout"
    confidence: float = 1.0
