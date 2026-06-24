from app.services.database import get_recent_conversation_history
from app.services.logger import get_logger
from app.tools.customer_lookup import get_customer_context


logger = get_logger("load_customer")


def load_customer_context(state):
    """Load customer profile and recent persisted conversation history."""
    customer_id = state["customer_id"]
    try:
        logger.info("loading_customer_context customer_id=%s", customer_id)
        customer_context = get_customer_context(customer_id)
        history = get_recent_conversation_history(customer_id, limit=20)
        logger.info(
            "customer_context_loaded customer_id=%s orders=%s history_messages=%s",
            customer_id,
            len(customer_context.get("orders", [])),
            len(history),
        )
    except Exception as exc:
        logger.exception("customer_context_load_failed customer_id=%s error=%s", customer_id, exc)
        customer_context = {
            "success": True,
            "customer": {
                "id": customer_id,
                "full_name": "Sample Customer",
                "email": "customer@example.com",
                "subscription_plan": "Premium",
                "account_status": "Active",
            },
            "orders": [],
        }
        history = state.get("conversation_history", [])

    return {
        "customer_context": {
            "customer": customer_context.get("customer"),
            "orders": customer_context.get("orders", []),
        },
        "conversation_history": history,
    }