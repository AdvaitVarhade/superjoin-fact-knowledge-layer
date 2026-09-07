import pytest
from fastapi.testclient import TestClient
from src.api.main import app, store

@pytest.fixture(scope="session", autouse=True)
def setup_store():
    store.load_starter_datasets()

client = TestClient(app)

def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"

def test_api_get_facts():
    res = client.get("/api/facts")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_api_get_relationships():
    res = client.get("/api/relationships")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_api_get_cases():
    res = client.get("/api/cases")
    assert res.status_code == 200
    cases = res.json()
    assert isinstance(cases, list)

def test_api_query():
    res = client.post("/api/query", json={"query": "revenue"})
    assert res.status_code == 200
    data = res.json()
    assert "query" in data
    assert "answer" in data

def test_api_get_knowledge_graph():
    res = client.get("/api/graph")
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data
    assert "links" in data
    assert "entities" in data
    assert len(data["nodes"]) > 0

def test_api_document_page_image_and_metadata():
    docs_res = client.get("/api/documents")
    assert docs_res.status_code == 200
    docs = docs_res.json()
    assert len(docs) > 0

    test_doc_id = docs[0]["document_id"]
    
    # Test metadata
    meta_res = client.get(f"/api/documents/{test_doc_id}/page/1/metadata")
    assert meta_res.status_code == 200
    meta = meta_res.json()
    assert meta["page_number"] == 1
    assert meta["total_pages"] >= 1
    assert meta["width"] > 0
    assert meta["height"] > 0

    # Test image rendering
    img_res = client.get(f"/api/documents/{test_doc_id}/page/1/image")
    assert img_res.status_code == 200
    assert img_res.headers["content-type"] == "image/png"
    assert len(img_res.content) > 1000  # valid PNG bytes
    assert "x-page-width" in img_res.headers
    assert "x-page-height" in img_res.headers

def test_api_get_charts_data_multi_entity():
    res = client.get("/api/analytics/charts")
    assert res.status_code == 200
    data = res.json()
    assert "fact_distribution" in data
    assert "delhivery" in data
    assert "apple" in data
    assert "tesla" in data
    assert "india_macro" in data
    assert data["apple"]["kpis"]["headline_rev"] == "$391.0 Billion"
    assert data["tesla"]["kpis"]["headline_rev"] == "$97.7 Billion"
    assert data["delhivery"]["kpis"]["headline_rev"] == "₹8,141 Cr"

    # Test filtered entity request
    res_apple = client.get("/api/analytics/charts?entity_id=apple")
    assert res_apple.status_code == 200
    data_apple = res_apple.json()
    assert data_apple["selected_entity"] == "apple"
    assert "segments" in data_apple["apple"]

def test_api_export_facts_csv():
    res = client.get("/api/export/facts.csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "attachment; filename=superjoin_facts_export_" in res.headers["content-disposition"]
    content = res.content.decode("utf-8-sig")
    lines = content.strip().split("\r\n") if "\r\n" in content else content.strip().split("\n")
    assert len(lines) > 1
    headers = lines[0].split(",")
    assert "fact_id" in headers
    assert "bbox_x0" in headers
    assert "bbox_y1" in headers
    assert "normalized_value" in headers

    # Test filtered export
    res_filtered = client.get("/api/export/facts.csv?entity=delhivery&metric=revenue")
    assert res_filtered.status_code == 200
    content_filtered = res_filtered.content.decode("utf-8-sig")
    assert "delhivery" in content_filtered

def test_api_export_audit_package_json():
    res = client.get("/api/export/audit-package.json")
    assert res.status_code == 200
    assert "application/json" in res.headers["content-type"]
    assert "attachment; filename=superjoin_audit_package_" in res.headers["content-disposition"]
    data = res.json()
    assert "export_metadata" in data
    assert "documents" in data
    assert "facts" in data
    assert "reconciliation_ledger" in data
    assert "showcase_case_studies" in data
    assert data["export_metadata"]["total_facts"] > 0
    assert data["export_metadata"]["total_documents"] > 0



