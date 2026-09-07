from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from src.models.fact import Fact
from src.models.relationship import Relationship

class CaseStudy(BaseModel):
    case_number: int  # 1, 2, 3, 4
    title: str
    description: str
    dataset: str  # 'delhivery' or 'india-macroeconomy'
    relationship: Optional[Relationship] = None
    source_fact: Optional[Fact] = None
    target_fact: Optional[Fact] = None
    system_reasoning: str
    resolution_status: str
