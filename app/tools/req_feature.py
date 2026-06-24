from app.services.linear import LinearService


def request_feature(
	customer_id: int,
	customer_tier: str,
	summary: str,
	details: str,
):
	linear_service = LinearService()
	result = linear_service.createFeatureRequestTicket(
		customer_id=customer_id,
		customer_tier=customer_tier,
		summary=summary,
		details=details,
	)

	if not result.get("success"):
		return {
			"success": False,
			"tool_name": "request_feature",
			"action": "create_feature_ticket",
			"message": "Failed to create feature request ticket.",
			"errors": result.get("errors", []),
		}

	return {
		"success": True,
		"tool_name": "request_feature",
		"action": "create_feature_ticket",
		"message": "Feature request ticket created.",
		"ticket": result.get("ticket", {}),
		"provider": result.get("provider", "linear"),
	}