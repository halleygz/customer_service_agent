from app.services.database import get_customer_context as _get_customer_context


def get_customer_context(customer_id: int):
    context = _get_customer_context(customer_id)
    customer = context.get("customer")
    if not customer:
        return {
            "success": False,
            "message": f"Customer {customer_id} was not found.",
            "customer": None,
            "orders": [],
        }

    return {
        "success": True,
        "message": "Customer context loaded.",
        "customer": customer,
        "orders": context.get("orders", []),
    }


