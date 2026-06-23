from services.database import get_connection


def get_customer_context(customer_id: int):

    conn = get_connection()

    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            full_name,
            email,
            subscription_plan,
            account_status
        FROM customers
        WHERE id = %s
        """,
        (customer_id,)
    )

    customer = cur.fetchone()

    cur.execute(
        """
        SELECT
            product_name,
            order_status,
            total
        FROM orders
        WHERE customer_id = %s
        """,
        (customer_id,)
    )

    orders = cur.fetchall()

    conn.close()

    return {
        "customer": customer,
        "orders": orders
    }


