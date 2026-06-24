from app.tools.req_feature import request_feature


def feature_request_agent(state):
    customer = (state.get("customer_context") or {}).get("customer") or {}
    customer_tier = customer.get("subscription_plan", "Unknown")
    message = state.get("customer_msg", "")

    result = request_feature(
        customer_id=state["customer_id"],
        customer_tier=customer_tier,
        summary=message[:120],
        details=message,
    )

    tool_results = list(state.get("tool_results", []))
    tool_results.append(result)

    if result.get("success"):
        ticket = result.get("ticket", {})
        ticket_ref = ticket.get("identifier", ticket.get("id", "N/A"))
        return {
            "assigned_agent": "feature_request",
            "tool_results": tool_results,
            "agent_response": (
                "Thanks for the suggestion. "
                f"I created a feature request ticket ({ticket_ref})."
            ),
            "status": "resolved",
        }

    return {
        "assigned_agent": "feature_request",
        "tool_results": tool_results,
        "agent_response": (
            "I captured your feature request, but ticket creation failed. "
            "I will escalate this to a human agent."
        ),
        "requires_human": True,
        "escalation_reason": "Failed to create feature request ticket.",
        "status": "needs_human",
    }
