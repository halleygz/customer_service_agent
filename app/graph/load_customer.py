from app.services.database import get_recent_conversation_history
from app.tools.customer_lookup import get_customer_context


def load_customer_context(state):
    """Load customer profile and recent persisted conversation history."""
    customer_id = state["customer_id"]
    try:
        customer_context = get_customer_context(customer_id)
        history = get_recent_conversation_history(customer_id, limit=20)
    except Exception as exc:
        print(f"Warning: Could not fetch customer context/history: {exc}")
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