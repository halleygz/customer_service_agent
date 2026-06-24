from typing import Any, Dict, List, Literal, Optional, TypedDict


Route = Literal[
    "billing",
    "technical_support",
    "feature_request",
    "general_inquiry",
    "escalation",
]


class RoutingDecision(TypedDict, total=False):
    route: Route
    reason: str
    confidence: float
    requires_human: bool


class ToolResult(TypedDict, total=False):
    tool_name: str
    success: bool
    action: str
    message: str
    data: Dict[str, Any]


class CustomerState(TypedDict, total=False):
    ticket_id: str
    conversation_id: str
    customer_id: int
    customer_msg: str
    customer_context: Optional[Dict[str, Any]]
    conversation_history: List[Dict[str, Any]]
    classification: Optional[RoutingDecision]
    selected_route: Optional[Route]
    previous_route: Optional[Route]
    handoff_note: Optional[str]
    assigned_agent: Optional[str]
    tool_results: List[ToolResult]
    requires_human: bool
    escalation_reason: Optional[str]
    escalation_id: Optional[int]
    support_summary: Optional[str]
    status: str
    agent_response: Optional[str]

