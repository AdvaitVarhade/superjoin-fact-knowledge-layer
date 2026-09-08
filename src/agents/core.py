"""
Core Agent Engine and ReAct Loop for Superjoin Multi-Agent Financial Audit Swarm.
Implements step-by-step reasoning, tool dispatch, thought trace logging, and citation tracking.
"""

import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from src.agents.tools import AgentToolRegistry


class AgentCitation(BaseModel):
    document_name: str
    document_id: Optional[str] = None
    page_number: int
    bbox: Optional[List[float]] = None
    snippet: Optional[str] = None
    metric: Optional[str] = None
    raw_value: Optional[str] = None


class AgentStep(BaseModel):
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    step_number: int
    step_type: str  # 'thought', 'action', 'observation', 'critic_review', 'delegation', 'final_answer'
    agent_role: str
    thought: Optional[str] = None
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[Any] = None
    content: Optional[str] = None
    citations: List[AgentCitation] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AgentMission(BaseModel):
    mission_id: str = Field(default_factory=lambda: f"mission_{str(uuid.uuid4())[:8]}")
    objective: str
    entity_target: Optional[str] = None
    status: str = "pending"  # 'pending', 'running', 'completed', 'failed'
    steps: List[AgentStep] = Field(default_factory=list)
    final_memo: Optional[str] = None
    citations: List[AgentCitation] = Field(default_factory=list)
    audit_score: Optional[float] = None
    start_time: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    completion_time: Optional[str] = None


class BaseAgent:
    """Base class for specialist agents in the audit swarm."""

    def __init__(self, role: str, description: str, tool_registry: AgentToolRegistry):
        self.role = role
        self.description = description
        self.tools = tool_registry

    def log_thought(self, mission: AgentMission, thought_text: str) -> AgentStep:
        step = AgentStep(
            step_number=len(mission.steps) + 1,
            step_type="thought",
            agent_role=self.role,
            thought=thought_text,
            content=thought_text
        )
        mission.steps.append(step)
        return step

    def execute_action(self, mission: AgentMission, tool_name: str, arguments: Dict[str, Any]) -> AgentStep:
        action_step = AgentStep(
            step_number=len(mission.steps) + 1,
            step_type="action",
            agent_role=self.role,
            tool_name=tool_name,
            tool_input=arguments,
            content=f"Invoking {tool_name}({arguments})"
        )
        mission.steps.append(action_step)

        # Execute tool
        output = self.tools.execute_tool(tool_name, arguments)

        # Extract citations if available
        citations = self._extract_citations(tool_name, output)

        obs_step = AgentStep(
            step_number=len(mission.steps) + 1,
            step_type="observation",
            agent_role=self.role,
            tool_name=tool_name,
            tool_output=output,
            content=f"Observation from {tool_name}: {self._summarize_output(output)}",
            citations=citations
        )
        mission.steps.append(obs_step)

        for c in citations:
            if not any(ec.document_name == c.document_name and ec.page_number == c.page_number and ec.snippet == c.snippet for ec in mission.citations):
                mission.citations.append(c)

        return obs_step

    def _extract_citations(self, tool_name: str, tool_output: Dict[str, Any]) -> List[AgentCitation]:
        citations = []
        if not tool_output.get("success", False):
            return citations

        res = tool_output.get("result", {})
        if isinstance(res, dict):
            # 1. Check facts array
            if "facts" in res and isinstance(res["facts"], list):
                for f in res["facts"]:
                    if f.get("document_name") and f.get("page_number"):
                        citations.append(AgentCitation(
                            document_name=f.get("document_name"),
                            document_id=f.get("document_id"),
                            page_number=f.get("page_number"),
                            bbox=f.get("bbox"),
                            snippet=f.get("snippet"),
                            metric=f.get("metric_id"),
                            raw_value=f.get("raw_value")
                        ))
            # 2. Check dual comparison
            if "fact_a" in res and "fact_b" in res:
                for k in ["fact_a", "fact_b"]:
                    fa = res[k]
                    if fa.get("document_name") and fa.get("page_number"):
                        citations.append(AgentCitation(
                            document_name=fa.get("document_name"),
                            document_id=fa.get("document_id"),
                            page_number=fa.get("page_number"),
                            bbox=fa.get("bbox"),
                            snippet=fa.get("snippet"),
                            raw_value=fa.get("raw_value")
                        ))
            # 3. Check document matches
            if "matches" in res and isinstance(res["matches"], list):
                for m in res["matches"]:
                    citations.append(AgentCitation(
                        document_name=m.get("document_name"),
                        document_id=m.get("document_id"),
                        page_number=m.get("page_number"),
                        bbox=m.get("bbox"),
                        snippet=m.get("text")
                    ))
        return citations

    def _summarize_output(self, output: Dict[str, Any]) -> str:
        if not output.get("success", False):
            return f"Error: {output.get('error', 'Unknown failure')}"
        res = output.get("result", {})
        if isinstance(res, dict):
            if "total_found" in res:
                return f"Found {res['total_found']} matching canonical facts."
            if "result" in res:
                return f"Computed result = {res.get('formatted_result', res['result'])}"
            if "relation_type" in res:
                return f"Classification: {res['relation_type']} (Delta: {res.get('delta_percent', 0.0)}%)"
            if "grounding_status" in res:
                return f"Grounding check: {res['grounding_status']} (Doc: {res.get('document_name')}, p.{res.get('page_number')})"
            if "total_matches" in res:
                return f"Found {res['total_matches']} textual occurrences in document."
        return str(res)[:200]
