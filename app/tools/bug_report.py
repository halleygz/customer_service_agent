from app.services.linear import LinearService


def bug_report(
	customer_id: int,
	customer_tier: str,
	summary: str,
	reproduction_steps: str,
):
	linear_service = LinearService()
	result = linear_service.createBugReportTicket(
		customer_id=customer_id,
		customer_tier=customer_tier,
		summary=summary,
		reproduction_steps=reproduction_steps,
	)

	if not result.get("success"):
		return {
			"success": False,
			"tool_name": "bug_report",
			"action": "create_bug_ticket",
			"message": "Failed to create bug report ticket.",
			"errors": result.get("errors", []),
		}

	return {
		"success": True,
		"tool_name": "bug_report",
		"action": "create_bug_ticket",
		"message": "Bug ticket created.",
		"ticket": result.get("ticket", {}),
		"provider": result.get("provider", "linear"),
	}