"""
Automated Test Suite for Superjoin Financial Spreadsheet Grid & Certified Audit Dossier
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.storage.spreadsheet_builder import SpreadsheetBuilder

client = TestClient(app)


def test_spreadsheet_entities_list():
    """Verify all 5 entities are registered with valid metadata."""
    entities = SpreadsheetBuilder.get_all_entities()
    assert len(entities) == 5
    entity_ids = [e["id"] for e in entities]
    assert "delhivery" in entity_ids
    assert "amazon" in entity_ids
    assert "apple" in entity_ids
    assert "tesla" in entity_ids
    assert "india_macro" in entity_ids


@pytest.mark.parametrize("entity_id", ["delhivery", "amazon", "apple", "tesla", "india_macro"])
def test_spreadsheet_workbook_structure(entity_id):
    """Verify workbook contains valid sheets, columns, rows, formulas, and BBox evidence."""
    wb = SpreadsheetBuilder.get_workbook(entity_id)
    assert wb is not None
    assert "sheets" in wb
    assert len(wb["sheets"]) >= 1

    # Inspect first sheet
    sheet1 = wb["sheets"][0]
    assert "columns" in sheet1
    assert "rows" in sheet1
    assert len(sheet1["columns"]) >= 4
    assert len(sheet1["rows"]) >= 3

    # Check evidence grounding in at least one cell
    has_evidence = False
    has_formula = False
    for row in sheet1["rows"]:
        for cell_key, cell_data in row.get("cells", {}).items():
            if isinstance(cell_data, dict):
                if "evidence" in cell_data and cell_data["evidence"]:
                    ev = cell_data["evidence"]
                    assert "document_name" in ev
                    assert "page_number" in ev
                    assert "bbox" in ev
                    assert len(ev["bbox"]) == 4
                    has_evidence = True
                if cell_data.get("is_formula") or cell_data.get("formula"):
                    has_formula = True

    assert has_evidence, f"Entity {entity_id} should contain cell-to-BBox evidence"
    assert has_formula, f"Entity {entity_id} should contain dynamic formula cells"


def test_api_spreadsheet_entities_endpoint():
    """Test GET /api/spreadsheet/entities."""
    res = client.get("/api/spreadsheet/entities")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 5


def test_api_spreadsheet_model_endpoint():
    """Test GET /api/spreadsheet/model."""
    for ent in ["delhivery", "amazon", "apple", "tesla", "india_macro"]:
        res = client.get(f"/api/spreadsheet/model?entity_id={ent}")
        assert res.status_code == 200
        data = res.json()
        assert data["entity_id"] == ent
        assert len(data["sheets"]) >= 1


def test_api_export_audit_dossier_html():
    """Test GET /api/export/audit-dossier."""
    res = client.get("/api/export/audit-dossier?entity_id=delhivery")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    html = res.text
    assert "SUPERJOIN FACT AUDIT DOSSIER" in html
    assert "Executive Provenance & Grounding Scorecard" in html
    assert "Audited Corporate Filings" in html
    assert "Multi-Agent Swarm Certification" in html
    assert "CERTIFIED AUDIT" in html
    assert "SHA256" in html
