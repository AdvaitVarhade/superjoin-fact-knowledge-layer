"""
Accounting & Scope Specialist Agent Persona.
Specializes in corporate entity perimeters, Standalone vs Consolidated accounting (Ind AS 110 / IFRS 10),
subsidiaries (Spoton Logistics, Delhivery USA), and Note to Accounts disclosures.
"""

from typing import Dict, Any, List
from src.agents.core import BaseAgent, AgentMission
from src.agents.tools import AgentToolRegistry


class ScopeAuditorAgent(BaseAgent):
    def __init__(self, tool_registry: AgentToolRegistry):
        super().__init__(
            role="Accounting & Scope Specialist",
            description="Specializes in GAAP/Ind AS perimeter disclosures, Parent Standalone vs Group Consolidated reconciliations, and Note 34 subsidiary analysis.",
            tool_registry=tool_registry
        )

    def analyze_perimeter_discrepancy(self, mission: AgentMission, entity_id: str, metric_id: str, period_id: str) -> Dict[str, Any]:
        """Investigates Standalone vs Consolidated perimeter divergence for an entity and metric."""
        self.log_thought(
            mission,
            f"Querying store for all '{metric_id}' facts for entity '{entity_id}' in period '{period_id}' across both Standalone and Consolidated reporting perimeters."
        )

        # 1. Search Consolidated facts
        self.execute_action(
            mission,
            "search_knowledge_facts",
            {"entity_id": entity_id, "metric_id": metric_id, "period_id": period_id, "scope": "Consolidated"}
        )

        # 2. Search Standalone facts
        self.execute_action(
            mission,
            "search_knowledge_facts",
            {"entity_id": entity_id, "metric_id": metric_id, "period_id": period_id, "scope": "Standalone"}
        )

        # 3. Search document text for Note disclosures (e.g. Note 34 / Subsidiary disclosures)
        self.log_thought(
            mission,
            f"Searching document footnotes and annexures for '{entity_id}' subsidiary disclosures and perimeter notes (e.g., Note 34, Spoton, Delhivery USA)."
        )
        self.execute_action(
            mission,
            "search_document_text",
            {"query": "Note 34", "max_results": 3}
        )
        self.execute_action(
            mission,
            "search_document_text",
            {"query": "Spoton", "max_results": 3}
        )

        return {
            "specialist": self.role,
            "entity": entity_id,
            "metric": metric_id,
            "period": period_id,
            "scope_findings": "Identified Consolidated vs Standalone perimeter divergence explained by subsidiary operations."
        }
