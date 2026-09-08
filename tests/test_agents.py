"""
Unit and Integration Tests for Superjoin Multi-Agent Financial Audit Subsystem.
Tests tool execution, multi-agent orchestration, critic verification, and streaming events.
"""

import pytest
from src.storage.store import FactKnowledgeStore
from src.agents.tools import AgentToolRegistry
from src.agents.orchestrator import AgentOrchestrator
from src.agents.personas.scope_auditor import ScopeAuditorAgent
from src.agents.personas.forensic_arithmetic import ForensicArithmeticAgent
from src.agents.personas.visual_critic import VisualCriticAgent


@pytest.fixture(scope="module")
def store():
    st = FactKnowledgeStore()
    st.load_starter_datasets()
    return st


@pytest.fixture(scope="module")
def tools(store):
    return AgentToolRegistry(store)


@pytest.fixture(scope="module")
def orchestrator(store):
    return AgentOrchestrator(store)


def test_tool_registry_schemas(tools):
    schemas = tools.get_tool_schemas()
    assert len(schemas) >= 8
    tool_names = [s["function"]["name"] for s in schemas]
    assert "search_knowledge_facts" in tool_names
    assert "get_fact_details" in tool_names
    assert "get_evidence_comparison" in tool_names
    assert "search_document_text" in tool_names
    assert "calculate_arithmetic" in tool_names
    assert "classify_reconciliation" in tool_names
    assert "verify_provenance_grounding" in tool_names
    assert "update_fact_audit_status" in tool_names


def test_tool_calculate_arithmetic(tools):
    # Test variance percentage
    res = tools.execute_tool("calculate_arithmetic", {
        "expression": "((8141 - 7542) / 8141) * 100",
        "operation_type": "variance_pct"
    })
    assert res["success"] is True
    assert round(res["result"]["result"], 2) == 7.36

    # Test EBITDA bridge
    res_bridge = tools.execute_tool("calculate_arithmetic", {
        "expression": "127 - (-154)",
        "operation_type": "ebitda_bridge"
    })
    assert res_bridge["success"] is True
    assert res_bridge["result"]["result"] == 281.0


def test_tool_search_knowledge_facts(tools):
    res = tools.execute_tool("search_knowledge_facts", {
        "entity_id": "delhivery",
        "metric_id": "revenue"
    })
    assert res["success"] is True
    assert res["result"]["total_found"] >= 1
    for fact in res["result"]["facts"]:
        assert "fact_id" in fact
        assert "raw_value" in fact
        assert fact["bbox"] is not None


def test_tool_classify_reconciliation(tools, store):
    all_facts = list(store.facts.values())
    assert len(all_facts) >= 2
    f1, f2 = all_facts[0], all_facts[1]
    res = tools.execute_tool("classify_reconciliation", {
        "fact_id_a": f1.fact_id,
        "fact_id_b": f2.fact_id
    })
    assert res["success"] is True
    assert "relation_type" in res["result"]
    assert "delta_percent" in res["result"]


def test_tool_verify_provenance_grounding(tools, store):
    all_facts = list(store.facts.values())
    first_fact = all_facts[0]
    res = tools.execute_tool("verify_provenance_grounding", {
        "fact_id": first_fact.fact_id
    })
    assert res["success"] is True
    assert res["result"]["verified"] is True
    assert res["result"]["grounding_status"] == "ZERO_HALLUCINATION_VERIFIED"


def test_orchestrator_ebitda_mission(orchestrator):
    mission = orchestrator.run_mission("Audit Delhivery FY24 EBITDA to Net Loss bridge")
    assert mission.status == "completed"
    assert len(mission.steps) >= 5
    assert mission.audit_score is not None
    assert mission.audit_score >= 90.0
    assert mission.final_memo is not None
    assert "Certified Audit Memorandum" in mission.final_memo


def test_orchestrator_scope_mission(orchestrator):
    mission = orchestrator.run_mission("Reconcile Delhivery Standalone vs Consolidated FY24 scope variance")
    assert mission.status == "completed"
    assert len(mission.citations) >= 1
    assert "Certified Audit Memorandum" in mission.final_memo


def test_orchestrator_stream_mission(orchestrator):
    events = list(orchestrator.stream_mission("Audit macroeconomic CPI inflation spread"))
    assert len(events) >= 4
    event_types = [e["event"] for e in events]
    assert "mission_started" in event_types
    assert "agent_step" in event_types
    assert "mission_completed" in event_types
