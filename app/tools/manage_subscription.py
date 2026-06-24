from app.services.database import get_current_subscription, update_subscription
from app.services.logger import get_logger


logger = get_logger("tool.manage_subscription")


def manage_subscription(customer_id: int, target_plan: str):
	logger.info("tool_invocation manage_subscription customer_id=%s target_plan=%s", customer_id, target_plan)
	current = get_current_subscription(customer_id)
	if not current:
		return {
			"success": False,
			"tool_name": "manage_subscription",
			"action": "update_subscription",
			"message": "Customer not found.",
		}

	result = update_subscription(customer_id=customer_id, target_plan=target_plan)
	logger.info("tool_result manage_subscription success=%s action=%s", result.get("success"), result.get("action"))
	result["tool_name"] = "manage_subscription"
	result["action"] = "update_subscription"
	result["current_plan"] = current
	return result