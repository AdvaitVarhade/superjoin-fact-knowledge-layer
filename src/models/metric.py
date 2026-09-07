from typing import Optional
from pydantic import BaseModel

class Metric(BaseModel):
    metric_id: str  # canonical ID, e.g., 'revenue', 'express_shipments', 'gdp_growth'
    canonical_name: str
    synonyms: list[str] = []
    category: str = 'financial'  # 'financial', 'operational', 'macroeconomic'
    default_unit: Optional[str] = None
    description: Optional[str] = None
