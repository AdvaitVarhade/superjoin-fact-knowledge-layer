from typing import Optional, List
from pydantic import BaseModel, Field

class Metric(BaseModel):
    metric_id: str
    name: str
    category: str = "Financial"  # Financial, Operational, Macroeconomic, Corporate
    default_unit: str = "INR"
    description: Optional[str] = None
    synonyms: List[str] = Field(default_factory=list)
