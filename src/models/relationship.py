from typing import Optional
from enum import Enum
from pydantic import BaseModel

class RelationType(str, Enum):
    CORROBORATION = "CORROBORATION"
    CONTRADICTION = "CONTRADICTION"
    RECONCILED_SCOPE = "RECONCILED_SCOPE"
    RECONCILED_TEMPORAL = "RECONCILED_TEMPORAL"
    RECONCILED_METHODOLOGY = "RECONCILED_METHODOLOGY"
    UNKNOWN = "UNKNOWN"

class Relationship(BaseModel):
    relationship_id: str
    fact_id_1: str
    fact_id_2: str
    relation_type: RelationType
    delta: Optional[float] = None
    delta_percent: Optional[float] = None
    explanation: str
    confidence: float = 1.0
    human_verified: bool = False
    resolution_notes: Optional[str] = None
