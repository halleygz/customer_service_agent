from app.services.database import get_current_subscription, update_subscription


def manage_subscription(customer_id: int, target_plan: str):
	current = get_current_subscription(customer_id)
	if not current:
		return {
			"success": False,
			"tool_name": "manage_subscription",
			"action": "update_subscription",
			"message": "Customer not found.",
		}

	result = update_subscription(customer_id=customer_id, target_plan=target_plan)
	result["tool_name"] = "manage_subscription"
	result["action"] = "update_subscription"
	result["current_plan"] = current
	return result