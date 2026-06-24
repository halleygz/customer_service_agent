from app.services.database import cancel_order


def manage_order(customer_id: int, order_id: int, action: str = "cancel"):
	normalized_action = (action or "").strip().lower()
	if normalized_action != "cancel":
		return {
			"success": False,
			"action": normalized_action,
			"message": "Unsupported order action. Only 'cancel' is currently supported.",
		}

	result = cancel_order(customer_id=customer_id, order_id=order_id)
	result["action"] = "cancel_order"
	result["tool_name"] = "manage_order"
	return result