from typing import List, Optional, Any
from pydantic import BaseModel
from src.models.evidence import Evidence
from src.models.period import Period

class Fact(BaseModel):
    fact_id: str
    entity_id: str
    metric_id: str
    period_id: str
    period: Period
    raw_value: str
    normalized_value: Optional[float] = None
    unit: Optional[str] = None
    currency: Optional[str] = None
    scope: str = 'Consolidated'  # 'Consolidated', 'Standalone', 'Segment', 'Macro'
    restatement_flag: bool = False
    evidence: List[Evidence]
    confidence: float = 1.0
    extraction_method: str = 'rule_regex'  # 'rule_regex', 'table_parser', 'llm'
    verification_status: str = 'PENDING'
