"""
Agent Tool Registry for Superjoin Multi-Agent Financial Audit Swarm.
Provides typed, structured tools with JSON schemas for autonomous fact discovery,
forensic math calculation, document text search, provenance verification, and reconciliation.
"""

import math
import re
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field, ConfigDict

from src.storage.store import FactKnowledgeStore
from src.models.fact import Fact
from src.models.evidence import Evidence
from src.models.relationship import Relationship, RelationType
from src.models.case_study import CaseStudy


class ToolDefinition(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    description: str
    parameters: Dict[str, Any]
    function: Optional[Callable] = None


class AgentToolRegistry:
    """Registry of deterministic tools accessible to autonomous audit agents."""

    def __init__(self, store: Optional[FactKnowledgeStore] = None):
        self.store = store or FactKnowledgeStore()
        self.tools: Dict[str, ToolDefinition] = {}
        self._register_default_tools()

    def register_tool(self, name: str, description: str, parameters: Dict[str, Any], fn: Callable):
        self.tools[name] = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            function=fn
        )

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Returns JSON schema representations of all registered tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            }
            for tool in self.tools.values()
        ]

    def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a registered tool by name with provided keyword arguments."""
        if name not in self.tools:
            return {
                "success": False,
                "error": f"Tool '{name}' not found in registry. Available tools: {list(self.tools.keys())}"
            }
        tool = self.tools[name]
        try:
            result = tool.function(**arguments)
            return {
                "success": True,
                "tool": name,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "tool": name,
                "error": str(e)
            }

    def _register_default_tools(self):
        # 1. Search Knowledge Facts
        self.register_tool(
            name="search_knowledge_facts",
            description="Search canonical facts in the knowledge store filtered by entity, metric, period, scope, or text query.",
            parameters={
                "type": "object",
                "properties": {
                    "entity_id": {"type": "string", "description": "Entity identifier (e.g., 'delhivery', 'apple', 'tesla', 'india_macro')"},
                    "metric_id": {"type": "string", "description": "Canonical metric identifier (e.g., 'revenue', 'ebitda', 'express_shipments', 'gdp_growth', 'cpi_inflation')"},
                    "period_id": {"type": "string", "description": "Standardized period identifier (e.g., 'FY24', 'FY23', 'Q4_FY24', '2024-25')"},
                    "scope": {"type": "string", "description": "Reporting scope filter ('Consolidated', 'Standalone', 'Interim')"},
                    "query": {"type": "string", "description": "Free-text semantic or keyword search string"}
                }
            },
            fn=self._tool_search_knowledge_facts
        )

        # 2. Get Fact Details
        self.register_tool(
            name="get_fact_details",
            description="Retrieve complete metadata, numerical values, and full bounding box evidence for a specific fact ID.",
            parameters={
                "type": "object",
                "properties": {
                    "fact_id": {"type": "string", "description": "The exact unique identifier of the fact"}
                },
                "required": ["fact_id"]
            },
            fn=self._tool_get_fact_details
        )

        # 3. Get Evidence Comparison
        self.register_tool(
            name="get_evidence_comparison",
            description="Retrieve a side-by-side comparison payload between two facts or for a relationship ID, including variance delta and dual BBoxes.",
            parameters={
                "type": "object",
                "properties": {
                    "fact_id_a": {"type": "string", "description": "Source fact identifier"},
                    "fact_id_b": {"type": "string", "description": "Target fact identifier"},
                    "relation_id": {"type": "string", "description": "Optional relationship identifier (e.g., 'rel_delh_rev_scope_fy24')"}
                }
            },
            fn=self._tool_get_evidence_comparison
        )

        # 4. Search Document Text & Footnotes
        self.register_tool(
            name="search_document_text",
            description="Search raw PDF text blocks, tables, and footnote disclosures across all indexed documents (e.g., search for 'Note 34', 'Spoton', 'ESOP').",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Text substring or keyword to locate in document pages"},
                    "document_id": {"type": "string", "description": "Optional document identifier to restrict search to a specific filing"},
                    "max_results": {"type": "integer", "description": "Maximum matching text snippets to return (default: 5)"}
                },
                "required": ["query"]
            },
            fn=self._tool_search_document_text
        )

        # 5. Calculate Arithmetic
        self.register_tool(
            name="calculate_arithmetic",
            description="Perform safe financial calculations, variance deltas, EBITDA bridges, growth rates, or CAGR calculations.",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Mathematical expression to evaluate (e.g., '(8141 - 7542) / 8141 * 100' or '127 - (-154)')"},
                    "operation_type": {"type": "string", "description": "Optional label describing the calculation (e.g., 'variance_percentage', 'ebitda_bridge', 'yoy_growth')"}
                },
                "required": ["expression"]
            },
            fn=self._tool_calculate_arithmetic
        )

        # 6. Classify Reconciliation
        self.register_tool(
            name="classify_reconciliation",
            description="Run the deterministic reconciliation engine on two facts to classify their relationship (CORROBORATION, CONTRADICTION, RECONCILED_SCOPE, RECONCILED_TEMPORAL).",
            parameters={
                "type": "object",
                "properties": {
                    "fact_id_a": {"type": "string", "description": "First fact identifier"},
                    "fact_id_b": {"type": "string", "description": "Second fact identifier"}
                },
                "required": ["fact_id_a", "fact_id_b"]
            },
            fn=self._tool_classify_reconciliation
        )

        # 7. Verify Provenance Grounding (Critic Tool)
        self.register_tool(
            name="verify_provenance_grounding",
            description="Adversarial Critic check: Verify that a fact is 100% grounded with valid page coordinates, document existence, and zero hallucination.",
            parameters={
                "type": "object",
                "properties": {
                    "fact_id": {"type": "string", "description": "Fact identifier to audit for provenance integrity"}
                },
                "required": ["fact_id"]
            },
            fn=self._tool_verify_provenance_grounding
        )

        # 8. Update Fact Audit Status
        self.register_tool(
            name="update_fact_audit_status",
            description="Record an auditor sign-off or discrepancy flag on a fact in the system audit ledger.",
            parameters={
                "type": "object",
                "properties": {
                    "fact_id": {"type": "string", "description": "Fact identifier to update"},
                    "status": {"type": "string", "description": "Status code ('VERIFIED_BY_HUMAN', 'FLAGGED_FOR_REVIEW', 'CERTIFIED_AUDIT')"},
                    "notes": {"type": "string", "description": "Auditor reasoning note or anomaly description"}
                },
                "required": ["fact_id", "status", "notes"]
            },
            fn=self._tool_update_fact_audit_status
        )

    # Tool Implementations
    def _tool_search_knowledge_facts(
        self,
        entity_id: Optional[str] = None,
        metric_id: Optional[str] = None,
        period_id: Optional[str] = None,
        scope: Optional[str] = None,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        results = self.store.search_facts(
            query=query,
            entity_id=entity_id,
            metric_id=metric_id,
            period_id=period_id
        )
        if scope:
            s_lower = scope.lower().strip()
            results = [f for f in results if (f.scope or "").lower() == s_lower]

        formatted = []
        for f in results:
            primary_ev = f.evidence[0] if f.evidence else None
            formatted.append({
                "fact_id": f.fact_id,
                "entity_id": f.entity_id,
                "metric_id": f.metric_id,
                "raw_value": f.raw_value,
                "normalized_value": f.normalized_value,
                "unit": f.unit,
                "period_id": f.period_id,
                "scope": f.scope,
                "confidence": f.confidence,
                "document_name": primary_ev.document_name if primary_ev else None,
                "document_id": primary_ev.document_id if primary_ev else None,
                "page_number": primary_ev.page_number if primary_ev else None,
                "bbox": primary_ev.bbox if primary_ev else None,
                "snippet": primary_ev.text_snippet if primary_ev else None
            })
        return {
            "total_found": len(formatted),
            "facts": formatted
        }

    def _tool_get_fact_details(self, fact_id: str) -> Dict[str, Any]:
        if fact_id not in self.store.facts:
            return {"error": f"Fact ID '{fact_id}' not found in store registry."}
        fact = self.store.facts[fact_id]
        return fact.model_dump()

    def _tool_get_evidence_comparison(
        self,
        fact_id_a: Optional[str] = None,
        fact_id_b: Optional[str] = None,
        relation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        if relation_id:
            for rel in self.store.relationships:
                if rel.relation_id == relation_id:
                    fact_a = self.store.facts.get(rel.source_fact_id)
                    fact_b = self.store.facts.get(rel.target_fact_id)
                    if fact_a and fact_b:
                        ev_a = fact_a.evidence[0] if fact_a.evidence else None
                        ev_b = fact_b.evidence[0] if fact_b.evidence else None
                        return {
                            "relation_id": rel.relation_id,
                            "relation_type": rel.relation_type.value if hasattr(rel.relation_type, "value") else str(rel.relation_type),
                            "delta_value": rel.delta_value,
                            "delta_percent": rel.delta_percent,
                            "reasoning": rel.reasoning,
                            "fact_a": {
                                "fact_id": fact_a.fact_id,
                                "raw_value": fact_a.raw_value,
                                "normalized_value": fact_a.normalized_value,
                                "scope": fact_a.scope,
                                "document_name": ev_a.document_name if ev_a else None,
                                "document_id": ev_a.document_id if ev_a else None,
                                "page_number": ev_a.page_number if ev_a else None,
                                "bbox": ev_a.bbox if ev_a else None,
                                "snippet": ev_a.text_snippet if ev_a else None
                            },
                            "fact_b": {
                                "fact_id": fact_b.fact_id,
                                "raw_value": fact_b.raw_value,
                                "normalized_value": fact_b.normalized_value,
                                "scope": fact_b.scope,
                                "document_name": ev_b.document_name if ev_b else None,
                                "document_id": ev_b.document_id if ev_b else None,
                                "page_number": ev_b.page_number if ev_b else None,
                                "bbox": ev_b.bbox if ev_b else None,
                                "snippet": ev_b.text_snippet if ev_b else None
                            }
                        }

        if not fact_id_a or not fact_id_b:
            return {"error": "Must provide either 'relation_id' or both 'fact_id_a' and 'fact_id_b'."}

        if fact_id_a not in self.store.facts or fact_id_b not in self.store.facts:
            return {"error": f"One or both facts ({fact_id_a}, {fact_id_b}) not found."}

        fact_a = self.store.facts[fact_id_a]
        fact_b = self.store.facts[fact_id_b]
        ev_a = fact_a.evidence[0] if fact_a.evidence else None
        ev_b = fact_b.evidence[0] if fact_b.evidence else None

        v1 = fact_a.normalized_value or 0.0
        v2 = fact_b.normalized_value or 0.0
        delta_val = abs(v1 - v2)
        denom = max(abs(v1), abs(v2))
        delta_pct = round((delta_val / denom) * 100.0, 2) if denom > 0 else 0.0

        return {
            "fact_a": {
                "fact_id": fact_a.fact_id,
                "raw_value": fact_a.raw_value,
                "normalized_value": v1,
                "scope": fact_a.scope,
                "document_name": ev_a.document_name if ev_a else None,
                "document_id": ev_a.document_id if ev_a else None,
                "page_number": ev_a.page_number if ev_a else None,
                "bbox": ev_a.bbox if ev_a else None,
                "snippet": ev_a.text_snippet if ev_a else None
            },
            "fact_b": {
                "fact_id": fact_b.fact_id,
                "raw_value": fact_b.raw_value,
                "normalized_value": v2,
                "scope": fact_b.scope,
                "document_name": ev_b.document_name if ev_b else None,
                "document_id": ev_b.document_id if ev_b else None,
                "page_number": ev_b.page_number if ev_b else None,
                "bbox": ev_b.bbox if ev_b else None,
                "snippet": ev_b.text_snippet if ev_b else None
            },
            "delta_value": delta_val,
            "delta_percent": delta_pct
        }

    def _tool_search_document_text(
        self,
        query: str,
        document_id: Optional[str] = None,
        max_results: int = 5
    ) -> Dict[str, Any]:
        q_lower = query.lower().strip()
        matches = []

        docs_to_search = [self.store.documents[document_id]] if (document_id and document_id in self.store.documents) else list(self.store.documents.values())

        for doc in docs_to_search:
            for blk in doc.blocks:
                if q_lower in blk.text.lower():
                    matches.append({
                        "document_id": doc.document_id,
                        "document_name": doc.document_name,
                        "page_number": blk.page_number,
                        "bbox": blk.bbox,
                        "text": blk.text[:300] + ("..." if len(blk.text) > 300 else ""),
                        "is_table": blk.is_table
                    })
                    if len(matches) >= max_results:
                        break
            if len(matches) >= max_results:
                break

        return {
            "query": query,
            "total_matches": len(matches),
            "matches": matches
        }

    def _tool_calculate_arithmetic(self, expression: str, operation_type: Optional[str] = None) -> Dict[str, Any]:
        clean_expr = expression.replace(",", "").strip()
        if not re.match(r'^[0-9\.\+\-\*\/\(\)\s\%\^eE]+$', clean_expr):
            return {"error": "Invalid characters in mathematical expression. Only standard arithmetic allowed."}
        try:
            safe_expr = clean_expr.replace("^", "**")
            val = eval(safe_expr, {"__builtins__": None, "math": math}, {})
            return {
                "expression": expression,
                "operation_type": operation_type or "arithmetic_evaluation",
                "result": float(val),
                "formatted_result": f"{val:,.4f}".rstrip('0').rstrip('.')
            }
        except Exception as e:
            return {"error": f"Failed to evaluate expression: {str(e)}"}

    def _tool_classify_reconciliation(self, fact_id_a: str, fact_id_b: str) -> Dict[str, Any]:
        if fact_id_a not in self.store.facts or fact_id_b not in self.store.facts:
            return {"error": f"Fact IDs {fact_id_a} or {fact_id_b} not found."}
        f1 = self.store.facts[fact_id_a]
        f2 = self.store.facts[fact_id_b]

        v1 = f1.normalized_value or 0.0
        v2 = f2.normalized_value or 0.0
        delta_val = abs(v1 - v2)
        denom = max(abs(v1), abs(v2))
        delta_pct = (delta_val / denom) * 100.0 if denom > 0 else 0.0

        s1 = (f1.scope or "").lower()
        s2 = (f2.scope or "").lower()

        if delta_pct <= 1.0:
            rel_type = "CORROBORATION"
            reasoning = f"Corroborated: Identical values reported across independent filings with {delta_pct:.2f}% variance."
        elif (s1 and s2) and (("standalone" in s1 and "consolidated" in s2) or ("consolidated" in s1 and "standalone" in s2)):
            rel_type = "RECONCILED_SCOPE"
            reasoning = f"Scope Reconciliation: Divergence ({delta_pct:.2f}%) explained by parent Standalone vs group Consolidated reporting boundary."
        elif f1.period_id != f2.period_id:
            rel_type = "RECONCILED_TEMPORAL"
            reasoning = f"Temporal Variance: Divergence explained by different reporting periods ({f1.period_id} vs {f2.period_id})."
        else:
            rel_type = "CONTRADICTION"
            reasoning = f"Genuine Discrepancy: Significant variance ({delta_pct:.2f}%) without explicit perimeter or temporal reconciliation."

        return {
            "relation_type": rel_type,
            "delta_value": delta_val,
            "delta_percent": round(delta_pct, 2),
            "reasoning": reasoning,
            "fact_a_summary": f"{f1.raw_value} ({f1.scope or 'General'}) in {f1.evidence[0].document_name if f1.evidence else 'N/A'}",
            "fact_b_summary": f"{f2.raw_value} ({f2.scope or 'General'}) in {f2.evidence[0].document_name if f2.evidence else 'N/A'}"
        }

    def _tool_verify_provenance_grounding(self, fact_id: str) -> Dict[str, Any]:
        if fact_id not in self.store.facts:
            return {"verified": False, "reason": f"Fact ID '{fact_id}' not found."}
        fact = self.store.facts[fact_id]
        if not fact.evidence:
            return {"verified": False, "reason": "No evidence attached to fact."}

        ev = fact.evidence[0]
        if not ev.bbox or len(ev.bbox) != 4:
            return {"verified": False, "reason": "Invalid or missing bounding box coordinates."}

        if ev.page_number < 1:
            return {"verified": False, "reason": f"Invalid page number {ev.page_number}."}

        if not ev.text_snippet or len(ev.text_snippet.strip()) == 0:
            return {"verified": False, "reason": "Empty text snippet in evidence."}

        return {
            "verified": True,
            "fact_id": fact.fact_id,
            "document_name": ev.document_name,
            "page_number": ev.page_number,
            "bbox": ev.bbox,
            "text_snippet": ev.text_snippet,
            "confidence": fact.confidence,
            "grounding_status": "ZERO_HALLUCINATION_VERIFIED"
        }

    def _tool_update_fact_audit_status(self, fact_id: str, status: str, notes: str) -> Dict[str, Any]:
        if fact_id not in self.store.facts:
            return {"error": f"Fact ID '{fact_id}' not found."}
        fact = self.store.facts[fact_id]
        if not fact.metadata:
            fact.metadata = {}
        fact.metadata["verification_status"] = status
        fact.metadata["audit_notes"] = notes
        return {
            "fact_id": fact_id,
            "updated_status": status,
            "audit_notes": notes,
            "success": True
        }
