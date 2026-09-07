# src/reconciliation/engine.py

- ReconciliationEngine · class · L8-L400 — class ReconciliationEngine:
- __init__ · method · L9-L10 — def __init__(self, tolerance_percent: float = 1.0):
- reconcile_facts · method · L12-L33 — def reconcile_facts(self, facts: List[Fact]) -> List[Relationship]:
- _compare_fact_pair · method · L35-L156 — def _compare_fact_pair(self, f1: Fact, f2: Fact, doc1: str, doc2: str) -> Optional[Relationship]:
- generate_showcase_cases · method · L158-L400 — def generate_showcase_cases(self, facts: List[Fact], relationships: List[Relationship]) -> List[CaseStudy]:
