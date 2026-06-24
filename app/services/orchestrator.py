import uuid
from typing import Any, Dict

from app.graph.builder import graph
from app.services.logger import get_logger


logger = get_logger("orchestrator")


def create_initial_state(customer_id: int, conversation_id: str | None = None) -> Dict[str, Any]:
    base_id = conversation_id or str(uuid.uuid4())[:8]
    return {
        "ticket_id": base_id,
        "conversation_id": base_id,
        "customer_id": customer_id,
        "customer_msg": "",
        "customer_context": None,
        "agent_response": None,
        "classification": None,
        "selected_route": None,
        "previous_route": None,
        "handoff_note": None,
        "assigned_agent": None,
        "tool_results": [],
        "requires_human": False,
        "status": "open",
        "escalation_reason": None,
        "escalation_id": None,
        "support_summary": None,
        "conversation_history": [],
    }


def prepare_turn_state(state: Dict[str, Any], customer_msg: str) -> Dict[str, Any]:
    next_state = dict(state)
    next_state["customer_msg"] = customer_msg
    next_state["tool_results"] = []
    next_state["requires_human"] = False
    next_state["escalation_reason"] = None
    next_state["status"] = "open"
    next_state["agent_response"] = None
    next_state["handoff_note"] = None
    next_state["previous_route"] = next_state.get("selected_route")
    return next_state


def run_customer_turn(state: Dict[str, Any], customer_msg: str) -> Dict[str, Any]:
    prepared_state = prepare_turn_state(state, customer_msg)
    logger.info(
        "incoming_message customer_id=%s conversation_id=%s text=%s",
        prepared_state.get("customer_id"),
        prepared_state.get("conversation_id"),
        customer_msg[:180],
    )

    result = graph.invoke(prepared_state)
    logger.info(
        "turn_completed customer_id=%s route=%s assigned_agent=%s status=%s",
        result.get("customer_id"),
        result.get("selected_route"),
        result.get("assigned_agent"),
        result.get("status"),
    )
    return result
