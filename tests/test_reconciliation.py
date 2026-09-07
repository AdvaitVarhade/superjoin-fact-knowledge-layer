import pytest
from src.models.fact import Fact
from src.models.evidence import Evidence
from src.models.relationship import RelationType
from src.reconciliation.engine import ReconciliationEngine

def test_corroboration_detection():
    engine = ReconciliationEngine()

    ev1 = Evidence(
        evidence_id="ev1", document_id="doc1", document_name="Annual_Report_FY24.pdf",
        page_number=10, bbox=[10.0, 10.0, 100.0, 50.0], text_snippet="Revenue was 8141 Cr"
    )
    ev2 = Evidence(
        evidence_id="ev2", document_id="doc2", document_name="Earnings_Q4_FY24.pdf",
        page_number=4, bbox=[20.0, 20.0, 120.0, 60.0], text_snippet="FY24 Revenue: Rs 8,141 Cr"
    )

    f1 = Fact(
        fact_id="f1", entity_id="delhivery", metric_id="revenue", period_id="FY24",
        raw_value="₹8,141 Cr", normalized_value=81410000000.0, unit="Cr", scope="Consolidated", evidence=[ev1]
    )
    f2 = Fact(
        fact_id="f2", entity_id="delhivery", metric_id="revenue", period_id="FY24",
        raw_value="₹8141 Cr", normalized_value=81410000000.0, unit="Cr", scope="Consolidated", evidence=[ev2]
    )

    rels = engine.reconcile_facts([f1, f2])
    assert len(rels) == 1
    assert rels[0].relation_type == RelationType.CORROBORATION
    assert rels[0].delta_percent == 0.0

def test_scope_reconciliation():
    engine = ReconciliationEngine()

    ev1 = Evidence(
        evidence_id="ev1", document_id="doc1", document_name="Annual_Report_FY24.pdf",
        page_number=10, bbox=[10.0, 10.0, 100.0, 50.0], text_snippet="Consolidated Revenue 8141 Cr"
    )
    ev2 = Evidence(
        evidence_id="ev2", document_id="doc2", document_name="Prospectus.pdf",
        page_number=12, bbox=[20.0, 20.0, 120.0, 60.0], text_snippet="Standalone Revenue 7542 Cr"
    )

    f1 = Fact(
        fact_id="f1", entity_id="delhivery", metric_id="revenue", period_id="FY24",
        raw_value="₹8,141 Cr", normalized_value=81410000000.0, unit="Cr", scope="Consolidated", evidence=[ev1]
    )
    f2 = Fact(
        fact_id="f2", entity_id="delhivery", metric_id="revenue", period_id="FY24",
        raw_value="₹7,542 Cr", normalized_value=75420000000.0, unit="Cr", scope="Standalone", evidence=[ev2]
    )

    rels = engine.reconcile_facts([f1, f2])
    assert len(rels) == 1
    assert rels[0].relation_type == RelationType.RECONCILED_SCOPE
