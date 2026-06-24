from app.services.llm import llm_service
from app.tools.manage_orders import manage_order
from app.tools.manage_subscription import manage_subscription


def billing_agent(state):
    customer_id = state["customer_id"]
    message = state.get("customer_msg", "")
    tool_results = list(state.get("tool_results", []))

    order_id = llm_service.extract_order_id(message)
    target_plan = llm_service.extract_target_plan(message)

    if order_id is not None and "cancel" in message.lower():
        result = manage_order(customer_id=customer_id, order_id=order_id, action="cancel")
        tool_results.append(result)
        if result.get("success"):
            return {
                "assigned_agent": "billing",
                "tool_results": tool_results,
                "agent_response": result["message"],
                "status": "resolved",
            }
        return {
            "assigned_agent": "billing",
            "tool_results": tool_results,
            "agent_response": (
                f"I could not cancel that order. {result.get('message', 'No details available.')}"
            ),
            "requires_human": True,
            "escalation_reason": "Order cancellation could not be completed automatically.",
            "status": "needs_human",
        }

    if target_plan is not None and any(token in message.lower() for token in ["upgrade", "downgrade", "plan", "subscription"]):
        result = manage_subscription(customer_id=customer_id, target_plan=target_plan)
        tool_results.append(result)
        if result.get("success"):
            return {
                "assigned_agent": "billing",
                "tool_results": tool_results,
                "agent_response": result["message"],
                "status": "resolved",
            }
        return {
            "assigned_agent": "billing",
            "tool_results": tool_results,
            "agent_response": (
                f"I could not update the subscription. {result.get('message', 'No details available.')}"
            ),
            "requires_human": True,
            "escalation_reason": "Subscription change could not be completed automatically.",
            "status": "needs_human",
        }

    guidance = llm_service.invoke_text(
        "You are a billing specialist for subscriptions and order support.",
        (
            f"Customer context: {state.get('customer_context')}\n"
            f"Message: {message}\n"
            "Provide concise billing guidance."
        ),
    )
    return {
        "assigned_agent": "billing",
        "tool_results": tool_results,
        "agent_response": guidance,
        "status": "resolved",
    }
