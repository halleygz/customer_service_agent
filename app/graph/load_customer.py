from tools.customer_lookup import get_customer_context


def load_customer_context(state):
    """Load customer context from database or return default if database unavailable."""
    try:
        customer_context = get_customer_context(
            state["customer_id"]
        )
    except Exception as e:
        # Handle database connection errors gracefully
        print(f"Warning: Could not fetch customer context: {e}")
        customer_context = {
            "customer": ("Sample Customer", "customer@example.com", "Premium", "Active"),
            "orders": [("Sample Product", "Completed", 99.99)]
        }

    return {
        "customer_context": customer_context
    }