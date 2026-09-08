"""
Automated Test Suite for Amazon.com, Inc. 3-Document Ingestion, Provenance Grounding,
Cross-Document Reconciliation, and Multi-Agent Swarm Audit.
"""

import os
import pytest
from src.storage.store import FactKnowledgeStore
from src.agents import AgentOrchestrator
from src.normalization.numbers import parse_number
from src.normalization.temporal import parse_period


@pytest.fixture(scope="module")
def store():
    st = FactKnowledgeStore()
    st.load_starter_datasets()
    return st


@pytest.fixture(scope="module")
def orchestrator(store):
    return AgentOrchestrator(store)


def test_amazon_documents_ingested(store):
    amazon_docs = [
        doc for doc in store.documents.values()
        if "amazon" in doc.document_id.lower() or "amazon" in doc.document_name.lower()
    ]
    assert len(amazon_docs) >= 3, f"Expected 3 Amazon documents, found {len(amazon_docs)}"
    for doc in amazon_docs:
        assert doc.total_pages > 0
        assert len(doc.blocks) > 0


def test_amazon_facts_extracted_with_provenance(store):
    amazon_facts = [f for f in store.facts.values() if f.entity_id == "amazon"]
    assert len(amazon_facts) >= 5, f"Expected >= 5 Amazon facts, found {len(amazon_facts)}"

    for fact in amazon_facts:
        assert fact.entity_id == "amazon"
        assert fact.normalized_value is not None
        assert fact.evidence is not None and len(fact.evidence) > 0

        # Check provenance grounding
        for ev in fact.evidence:
            assert ev.document_name is not None
            assert ev.page_number >= 1
            assert ev.bbox is not None and len(ev.bbox) == 4
            assert ev.text_snippet is not None and len(ev.text_snippet.strip()) > 0


def test_amazon_cross_document_reconciliation(store):
    amazon_rels = [r for r in store.relationships if r.entity_id == "amazon"]
    assert len(amazon_rels) >= 1, "Expected cross-document reconciliation relationships for Amazon"

    for rel in amazon_rels:
        assert rel.source_document != ""
        assert rel.target_document != ""
        assert rel.delta_percent is not None
        assert rel.reasoning != ""


def test_amazon_multi_agent_mission(orchestrator):
    mission = orchestrator.run_mission("Audit Amazon Net Sales and Operating Income across 2023 and 2024 Form 10-K filings")
    assert mission.status == "completed"
    assert len(mission.steps) >= 4
    assert mission.audit_score is not None
    assert mission.audit_score >= 90.0
    assert mission.final_memo is not None
    assert "Certified Audit Memorandum" in mission.final_memo
