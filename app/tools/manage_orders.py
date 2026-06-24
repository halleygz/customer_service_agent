from app.services.database import cancel_order
from app.services.logger import get_logger


logger = get_logger("tool.manage_order")


def manage_order(customer_id: int, order_id: int, action: str = "cancel"):
	logger.info("tool_invocation manage_order customer_id=%s order_id=%s action=%s", customer_id, order_id, action)
	normalized_action = (action or "").strip().lower()
	if normalized_action != "cancel":
		return {
			"success": False,
			"action": normalized_action,
			"message": "Unsupported order action. Only 'cancel' is currently supported.",
		}

	result = cancel_order(customer_id=customer_id, order_id=order_id)
	logger.info("tool_result manage_order success=%s message=%s", result.get("success"), result.get("message"))
	result["action"] = "cancel_order"
	result["tool_name"] = "manage_order"
	return result