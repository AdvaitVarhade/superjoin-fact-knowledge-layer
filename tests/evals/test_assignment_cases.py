import os
import pytest
from src.storage.store import FactKnowledgeStore
from src.models.relationship import RelationType

def test_full_assignment_four_cases():
    store = FactKnowledgeStore()
    store.load_starter_datasets()

    cases = store.case_studies
    assert len(cases) >= 4, f"Expected 4 showcase cases, found {len(cases)}"

    # 1. Verify Case 1 (Corroboration)
    c1 = next((c for c in cases if c.case_number == 1), None)
    assert c1 is not None, "Case 1: Corroboration missing"
    assert c1.relationship is not None
    assert c1.relationship.relation_type == RelationType.CORROBORATION
    assert c1.source_fact is not None
    assert c1.target_fact is not None
    assert len(c1.source_fact.evidence) > 0
    assert len(c1.target_fact.evidence) > 0

    # 2. Verify Case 2 (Contradiction)
    c2 = next((c for c in cases if c.case_number == 2), None)
    assert c2 is not None, "Case 2: Contradiction missing"
    assert c2.relationship is not None
    assert c2.relationship.relation_type == RelationType.CONTRADICTION

    # 3. Verify Case 3 (Context-Reconciled Contradiction)
    c3 = next((c for c in cases if c.case_number == 3), None)
    assert c3 is not None, "Case 3: Reconciled Contradiction missing"
    assert c3.relationship is not None
    assert c3.relationship.relation_type in [
        RelationType.RECONCILED_SCOPE,
        RelationType.RECONCILED_TEMPORAL,
        RelationType.RECONCILED_REVISION,
    ]

    # 4. Verify Case 4 (Handled Failure / Edge Case)
    c4 = next((c for c in cases if c.case_number == 4), None)
    assert c4 is not None, "Case 4: Handled Edge Case missing"
    assert "EDGE_CASE" in c4.resolution_status
