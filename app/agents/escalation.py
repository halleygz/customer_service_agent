from app.services.database import create_escalation
from app.services.logger import get_logger


logger = get_logger("escalation")


def escalation_agent(state):
	context = state.get("customer_context") or {}
	customer = context.get("customer") or {}
	tool_results = state.get("tool_results", [])

	ticket_notes = []
	for result in tool_results:
		ticket = result.get("ticket") if isinstance(result, dict) else None
		if ticket:
			ticket_notes.append(
				{
					"tool": result.get("tool_name"),
					"identifier": ticket.get("identifier", ticket.get("id", "N/A")),
					"url": ticket.get("url"),
				}
			)

	primary_ticket = ticket_notes[0] if ticket_notes else {}

	summary = {
		"customer_id": state.get("customer_id"),
		"customer_name": customer.get("full_name"),
		"subscription_tier": customer.get("subscription_plan"),
		"issue_type": state.get("selected_route"),
		"customer_request": state.get("customer_msg"),
		"classification": state.get("classification"),
		"actions_attempted": [
			{
				"tool": item.get("tool_name"),
				"action": item.get("action"),
				"success": item.get("success"),
				"message": item.get("message"),
			}
			for item in tool_results
			if isinstance(item, dict)
		],
		"tickets_created": ticket_notes,
		"unresolved_blocker": state.get("escalation_reason") or "Customer requested human support.",
	}

	escalation_row = create_escalation(
		customer_id=state.get("customer_id"),
		ticket_id=state.get("ticket_id"),
		route=state.get("selected_route"),
		summary=str(summary),
		linear_ticket_identifier=primary_ticket.get("identifier"),
		linear_ticket_url=primary_ticket.get("url"),
	)
	logger.info(
		"escalation_handoff escalation_id=%s customer_id=%s route=%s",
		escalation_row.get("id"),
		state.get("customer_id"),
		state.get("selected_route"),
	)

	return {
		"assigned_agent": "escalation",
		"escalation_id": escalation_row.get("id"),
		"status": "escalated",
		"requires_human": True,
		"support_summary": str(summary),
		"agent_response": (
			"I am escalating this conversation to a human support specialist now. "
			"I have included a concise handoff summary so they can continue without repeating steps."
		),
	}
