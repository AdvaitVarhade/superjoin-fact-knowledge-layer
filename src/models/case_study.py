from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from src.models.fact import Fact
from src.models.relationship import Relationship

class CaseStudy(BaseModel):
    case_number: int  # 1, 2, 3, 4
    title: str
    description: str
    dataset: str  # 'delhivery' or 'macro'
    source_facts: List[Fact]
    relationships: List[Relationship]
    reconciliation_summary: str
    resolution_status: str  # 'RECONCILED', 'CONTRADICTION_FLAGGED', 'CORROBORATED'
