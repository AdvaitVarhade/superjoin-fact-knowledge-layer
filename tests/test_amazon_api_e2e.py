"""
Comprehensive E2E API Test Suite for Amazon.com 3-Document Ingestion & Capabilities:
- Document Indexing & Page Parsing
- Fact Knowledge Search & Provenance Grounding
- Cross-Document Multi-Year Reconciliation Ledger
- D3 Knowledge Graph Generation
- Multi-Agent Swarm Mission Execution
- Audit & Financial Summaries Export
- Conversational AI Copilot Querying
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app


@pytest.fixture(scope="module")
def client():
    from src.api.main import store
    if len([d for d in store.documents.values() if "amazon" in d.document_id.lower() or "amazon" in d.document_name.lower()]) < 3:
        store.load_starter_datasets()
    with TestClient(app) as c:
        yield c


def test_api_documents_contains_amazon(client):
    response = client.get("/api/documents")
    assert response.status_code == 200
    docs = response.json()
    assert isinstance(docs, list)
    amazon_docs = [d for d in docs if "amazon" in d["document_id"].lower() or "amazon" in d["document_name"].lower()]
    assert len(amazon_docs) >= 3, f"Expected >= 3 Amazon documents, got {len(amazon_docs)}"


def test_api_facts_amazon_entity(client):
    response = client.get("/api/facts?entity=amazon")
    assert response.status_code == 200
    facts = response.json()
    assert isinstance(facts, list)
    assert len(facts) >= 5, f"Expected >= 5 Amazon facts, got {len(facts)}"
    
    # Verify provenance grounding on facts
    for f in facts[:5]:
        assert f["entity_id"] == "amazon"
        assert f["normalized_value"] is not None
        assert len(f["evidence"]) > 0
        ev = f["evidence"][0]
        assert ev["page_number"] >= 1
        assert len(ev["bbox"]) == 4
        assert ev["text_snippet"] != ""


def test_api_relationships_amazon(client):
    response = client.get("/api/relationships")
    assert response.status_code == 200
    rels = response.json()
    assert isinstance(rels, list)
    amazon_rels = [r for r in rels if r["entity_id"] == "amazon"]
    assert len(amazon_rels) >= 1, "Expected cross-document reconciliation links for Amazon"


def test_api_graph_amazon(client):
    response = client.get("/api/graph?entity_id=amazon")
    assert response.status_code == 200
    graph = response.json()
    assert "nodes" in graph
    assert "links" in graph
    assert len(graph["nodes"]) > 0
    assert len(graph["links"]) > 0


def test_api_copilot_chat_amazon(client):
    response = client.post("/api/copilot/chat", json={"message": "What were Amazon Net Sales in 2023?"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["citations"]) > 0


def test_api_agent_mission_amazon(client):
    payload = {
        "objective": "Audit Amazon Net Sales and Operating Income across 2023 and 2024 Form 10-K filings",
        "entity_target": "amazon"
    }
    response = client.post("/api/agent/run", json=payload)
    assert response.status_code == 200
    mission = response.json()
    assert mission["status"] == "completed"
    assert mission["audit_score"] >= 90.0
    assert "Certified Audit Memorandum" in mission["final_memo"]
    assert len(mission["steps"]) >= 4


def test_api_export_facts_csv(client):
    response = client.get("/api/export/facts.csv?entity=amazon")
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
    assert len(response.content) > 100


def test_api_export_audit_package(client):
    response = client.get("/api/export/audit-package.json")
    assert response.status_code == 200
    pkg = response.json()
    assert "export_metadata" in pkg
    assert "documents" in pkg
    assert "facts" in pkg
    assert "reconciliation_ledger" in pkg


def test_api_audit_risk_scorecard(client):
    response = client.get("/api/audit/risk-scorecard")
    assert response.status_code == 200
    data = response.json()
    assert "audit_health_score" in data
    assert data["audit_health_score"] >= 70.0
    assert "high_risk_items" in data
    assert "remediation_checklist" in data
