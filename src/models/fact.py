from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from src.models.evidence import Evidence
from src.models.entity import Entity
from src.models.metric import Metric
from src.models.period import Period

class Fact(BaseModel):
    fact_id: str
    entity_id: str
    metric_id: str
    period_id: str
    raw_value: str
    normalized_value: float
    unit: str  # INR, Cr, Lakh, %, USD, count, etc.
    scope: str = "Consolidated"  # Consolidated, Standalone, Segment, Total, etc.
    segment: Optional[str] = None  # e.g., Express Parcel, PTL, Supply Chain
    confidence: float = 1.0
    evidence: List[Evidence] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
