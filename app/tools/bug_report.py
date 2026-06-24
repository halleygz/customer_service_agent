from app.services.linear import LinearService
from app.services.logger import get_logger


logger = get_logger("tool.bug_report")


def bug_report(
	customer_id: int,
	customer_tier: str,
	summary: str,
	reproduction_steps: str,
):
	logger.info("tool_invocation bug_report customer_id=%s", customer_id)
	linear_service = LinearService()
	result = linear_service.createBugReportTicket(
		customer_id=customer_id,
		customer_tier=customer_tier,
		summary=summary,
		reproduction_steps=reproduction_steps,
	)

	if not result.get("success"):
		logger.error("tool_result bug_report success=false errors=%s", result.get("errors"))
		return {
			"success": False,
			"tool_name": "bug_report",
			"action": "create_bug_ticket",
			"message": "Failed to create bug report ticket.",
			"errors": result.get("errors", []),
		}

	logger.info("tool_result bug_report success=true ticket=%s", result.get("ticket", {}).get("identifier"))
	return {
		"success": True,
		"tool_name": "bug_report",
		"action": "create_bug_ticket",
		"message": "Bug ticket created.",
		"ticket": result.get("ticket", {}),
		"provider": result.get("provider", "linear"),
	}