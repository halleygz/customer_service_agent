from app.services.linear import LinearService
from app.services.logger import get_logger


logger = get_logger("tool.request_feature")


def request_feature(
	customer_id: int,
	customer_tier: str,
	summary: str,
	details: str,
):
	logger.info("tool_invocation request_feature customer_id=%s", customer_id)
	linear_service = LinearService()
	result = linear_service.createFeatureRequestTicket(
		customer_id=customer_id,
		customer_tier=customer_tier,
		summary=summary,
		details=details,
	)

	if not result.get("success"):
		logger.error("tool_result request_feature success=false errors=%s", result.get("errors"))
		return {
			"success": False,
			"tool_name": "request_feature",
			"action": "create_feature_ticket",
			"message": "Failed to create feature request ticket.",
			"errors": result.get("errors", []),
		}

	logger.info("tool_result request_feature success=true ticket=%s", result.get("ticket", {}).get("identifier"))
	return {
		"success": True,
		"tool_name": "request_feature",
		"action": "create_feature_ticket",
		"message": "Feature request ticket created.",
		"ticket": result.get("ticket", {}),
		"provider": result.get("provider", "linear"),
	}