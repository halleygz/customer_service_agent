from langgraph.graph import (
    StateGraph,
    START,
    END
)

from app.agents.escalation import escalation_agent
from app.agents.specialists.billing import billing_agent
from app.agents.specialists.feature import feature_request_agent
from app.graph.state import CustomerState
from app.services.database import store_conversation_message, store_support_event

from app.graph.load_customer import (
    load_customer_context
)

from app.agents.specialists.techincal import technical_support_agent
from app.agents.specialists.general import (
    general_support_agent
)
from app.agents.supervisor import classify_request
from app.services.logger import get_logger


logger = get_logger("graph")


def route_after_classification(state: CustomerState):
    logger.info(
        "route_selected route=%s previous=%s handoff=%s",
        state.get("selected_route"),
        state.get("previous_route"),
        state.get("handoff_note"),
    )
    return state.get("selected_route", "general_inquiry")


def route_after_specialist(state: CustomerState):
    if state.get("requires_human"):
        logger.info("specialist_requested_escalation assigned_agent=%s", state.get("assigned_agent"))
        return "escalation"
    return "persist_interaction"


def persist_interaction(state: CustomerState):
    customer_id = state["customer_id"]
    ticket_id = state["ticket_id"]
    conversation_id = state.get("conversation_id") or ticket_id

    customer_msg = state.get("customer_msg", "")
    agent_response = state.get("agent_response", "")

    try:
        logger.info(
            "persist_interaction customer_id=%s ticket_id=%s route=%s status=%s",
            customer_id,
            ticket_id,
            state.get("selected_route"),
            state.get("status"),
        )
        if customer_msg:
            store_conversation_message(
                customer_id=customer_id,
                ticket_id=conversation_id,
                role="customer",
                content=customer_msg,
                metadata={"route": state.get("selected_route")},
            )

        if agent_response:
            store_conversation_message(
                customer_id=customer_id,
                ticket_id=conversation_id,
                role="agent",
                content=agent_response,
                metadata={"status": state.get("status")},
            )

        classification = state.get("classification")
        if classification:
            store_support_event(
                customer_id=customer_id,
                ticket_id=conversation_id,
                event_type="classification",
                details=classification,
            )

        for result in state.get("tool_results", []):
            if isinstance(result, dict):
                store_support_event(
                    customer_id=customer_id,
                    ticket_id=conversation_id,
                    event_type="tool_action",
                    details=result,
                )

        if state.get("status") == "escalated":
            store_support_event(
                customer_id=customer_id,
                ticket_id=conversation_id,
                event_type="escalation",
                details={
                    "reason": state.get("escalation_reason"),
                    "summary": state.get("support_summary"),
                    "escalation_id": state.get("escalation_id"),
                },
            )
    except Exception as exc:
        logger.exception("persist_interaction_failed error=%s", exc)

    return {
        "conversation_id": conversation_id,
        "status": state.get("status", "resolved"),
    }

builder = StateGraph(CustomerState)

builder.add_node(
    "load_customer_context",
    load_customer_context
)

builder.add_node(
    "classify_request",
    classify_request
)

builder.add_node(
    "billing_agent",
    billing_agent
)

builder.add_node(
    "technical_support_agent",
    technical_support_agent
)

builder.add_node(
    "feature_request_agent",
    feature_request_agent
)

builder.add_node(
    "general_support_agent",
    general_support_agent
)

builder.add_node(
    "escalation_agent",
    escalation_agent
)

builder.add_node(
    "persist_interaction",
    persist_interaction
)

builder.add_edge(
    START,
    "load_customer_context"
)

builder.add_edge(
    "load_customer_context",
    "classify_request"
)

builder.add_conditional_edges(
    "classify_request",
    route_after_classification,
    {
        "billing": "billing_agent",
        "technical_support": "technical_support_agent",
        "feature_request": "feature_request_agent",
        "general_inquiry": "general_support_agent",
        "escalation": "escalation_agent",
    },
)

builder.add_conditional_edges(
    "billing_agent",
    route_after_specialist,
    {
        "escalation": "escalation_agent",
        "persist_interaction": "persist_interaction",
    },
)

builder.add_conditional_edges(
    "technical_support_agent",
    route_after_specialist,
    {
        "escalation": "escalation_agent",
        "persist_interaction": "persist_interaction",
    },
)

builder.add_conditional_edges(
    "feature_request_agent",
    route_after_specialist,
    {
        "escalation": "escalation_agent",
        "persist_interaction": "persist_interaction",
    },
)

builder.add_conditional_edges(
    "general_support_agent",
    route_after_specialist,
    {
        "escalation": "escalation_agent",
        "persist_interaction": "persist_interaction",
    },
)

builder.add_edge(
    "escalation_agent",
    "persist_interaction"
)

builder.add_edge(
    "persist_interaction",
    END
)

graph = builder.compile()