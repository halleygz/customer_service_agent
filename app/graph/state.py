from typing import Optional, TypedDict, List, Any


class CustomerState(TypedDict):
    ticket_id: str
    customer_id: str
    customer_msg: str
    category: Optional[str]
    assigned_agent: Optional[str]
    status: str
    escalation_reason: str
    conversation_history: List[dict]
    customer_context: Optional[Any]
    agent_response: Optional[str]

