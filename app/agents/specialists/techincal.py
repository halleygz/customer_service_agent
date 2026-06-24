from app.services.llm import llm_service
from app.tools.bug_report import bug_report


def technical_support_agent(state):
    customer = (state.get("customer_context") or {}).get("customer") or {}
    customer_tier = customer.get("subscription_plan", "Unknown")
    message = state.get("customer_msg", "")
    lowered = message.lower()

    tool_results = list(state.get("tool_results", []))

    # Basic triage before filing engineering tickets.
    maybe_bug = any(token in lowered for token in ["bug", "error", "crash", "not working", "broken"])
    can_offer_quick_fix = any(token in lowered for token in ["login", "password", "cache", "reset"]) and not maybe_bug

    if can_offer_quick_fix:
        response = (
            "Try signing out and back in, then clear app/browser cache and retry. "
            "If the issue persists, share exact steps and error text so I can investigate further."
        )
        return {
            "assigned_agent": "technical_support",
            "tool_results": tool_results,
            "agent_response": response,
            "status": "resolved",
        }

    if maybe_bug:
        bug_result = bug_report(
            customer_id=state["customer_id"],
            customer_tier=customer_tier,
            summary=message[:120],
            reproduction_steps=message,
        )
        tool_results.append(bug_result)

        if bug_result.get("success"):
            ticket = bug_result.get("ticket", {})
            ticket_ref = ticket.get("identifier", ticket.get("id", "N/A"))
            return {
                "assigned_agent": "technical_support",
                "tool_results": tool_results,
                "agent_response": (
                    "I could not safely resolve this in-chat, so I filed a bug ticket "
                    f"for engineering ({ticket_ref}). A human agent can follow up if needed."
                ),
                "requires_human": False,
                "status": "resolved",
            }

        return {
            "assigned_agent": "technical_support",
            "tool_results": tool_results,
            "agent_response": (
                "I could not resolve this technical issue automatically. "
                "I will escalate you to a human support specialist."
            ),
            "requires_human": True,
            "escalation_reason": "Technical issue unresolved and bug ticket creation failed.",
            "status": "needs_human",
        }

    response = llm_service.invoke_text(
        "You are a technical support specialist for an e-commerce SaaS product.",
        (
            f"Customer context: {state.get('customer_context')}\n"
            f"Message: {message}\n"
            "Provide practical troubleshooting steps and keep it concise."
        ),
    )
    return {
        "assigned_agent": "technical_support",
        "tool_results": tool_results,
        "agent_response": response,
        "status": "resolved",
    }
