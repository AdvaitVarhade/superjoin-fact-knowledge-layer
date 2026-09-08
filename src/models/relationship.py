from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class RelationType(str, Enum):
    CORROBORATION = "CORROBORATION"
    CONTRADICTION = "CONTRADICTION"
    RECONCILED_TEMPORAL = "RECONCILED_TEMPORAL"
    RECONCILED_SCOPE = "RECONCILED_SCOPE"
    RECONCILED_UNIT = "RECONCILED_UNIT"
    RECONCILED_REVISION = "RECONCILED_REVISION"
    EDGE_CASE_HANDLED = "EDGE_CASE_HANDLED"

class Relationship(BaseModel):
    relation_id: str
    relation_type: RelationType
    source_fact_id: str
    target_fact_id: str
    source_document: str
    target_document: str
    metric_id: str
    entity_id: str
    delta_value: Optional[float] = None
    delta_percent: Optional[float] = None
    confidence: float = 1.0
    reasoning: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def delta_percentage(self) -> Optional[float]:
        return self.delta_percent
