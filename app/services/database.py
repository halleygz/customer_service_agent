import os
from typing import Any, Dict, List, Optional, Tuple

import psycopg2
from psycopg2.extras import Json, RealDictCursor


VALID_PLANS = ["Free", "Premium", "Enterprise"]
PLAN_RANK = {"Free": 0, "Premium": 1, "Enterprise": 2}


def get_connection():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "halley's"),
        dbname=os.getenv("DB_NAME", "customer_support"),
    )
    ensure_support_tables(conn)
    return conn


def ensure_support_tables(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_messages (
                id SERIAL PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                ticket_id TEXT NOT NULL,
                message_role TEXT NOT NULL,
                message_content TEXT NOT NULL,
                metadata JSONB,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS support_events (
                id SERIAL PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                ticket_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                details JSONB,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
    conn.commit()


def get_customer_context(customer_id: int) -> Dict[str, Any]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, full_name, email, subscription_plan, account_status
                FROM customers
                WHERE id = %s
                """,
                (customer_id,),
            )
            customer = cur.fetchone()

            cur.execute(
                """
                SELECT id, product_name, order_status, total
                FROM orders
                WHERE customer_id = %s
                ORDER BY id DESC
                """,
                (customer_id,),
            )
            orders = cur.fetchall()

        return {
            "customer": dict(customer) if customer else None,
            "orders": [dict(order) for order in orders],
        }
    finally:
        conn.close()


def get_customer_orders(customer_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, customer_id, product_name, order_status, total
                FROM orders
                WHERE customer_id = %s
                ORDER BY id DESC
                """,
                (customer_id,),
            )
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    finally:
        conn.close()


def is_order_cancellable(order_status: str) -> bool:
    normalized = (order_status or "").strip().lower()
    return normalized in {"pending", "processing"}


def cancel_order(customer_id: int, order_id: int) -> Dict[str, Any]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, customer_id, product_name, order_status, total
                FROM orders
                WHERE id = %s
                """,
                (order_id,),
            )
            order = cur.fetchone()
            if not order:
                return {"success": False, "message": "Order not found."}

            if order["customer_id"] != customer_id:
                return {
                    "success": False,
                    "message": "This order does not belong to this customer.",
                }

            if not is_order_cancellable(order["order_status"]):
                return {
                    "success": False,
                    "message": (
                        f"Order {order_id} cannot be cancelled because its current "
                        f"status is '{order['order_status']}'."
                    ),
                    "order": dict(order),
                }

            cur.execute(
                """
                UPDATE orders
                SET order_status = 'Cancelled'
                WHERE id = %s
                RETURNING id, customer_id, product_name, order_status, total
                """,
                (order_id,),
            )
            updated = cur.fetchone()
        conn.commit()

        return {
            "success": True,
            "message": f"Order {order_id} was cancelled successfully.",
            "order": dict(updated),
        }
    finally:
        conn.close()


def get_current_subscription(customer_id: int) -> Optional[str]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT subscription_plan
                FROM customers
                WHERE id = %s
                """,
                (customer_id,),
            )
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        conn.close()


def validate_subscription_transition(
    current_plan: str, target_plan: str
) -> Tuple[bool, str, str]:
    if target_plan not in VALID_PLANS:
        return False, "invalid", f"'{target_plan}' is not a valid plan."

    if current_plan == target_plan:
        return False, "noop", "Customer is already on that plan."

    if PLAN_RANK[target_plan] > PLAN_RANK[current_plan]:
        return True, "upgrade", "Valid upgrade transition."

    return True, "downgrade", "Valid downgrade transition."


def update_subscription(customer_id: int, target_plan: str) -> Dict[str, Any]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT subscription_plan
                FROM customers
                WHERE id = %s
                """,
                (customer_id,),
            )
            row = cur.fetchone()
            if not row:
                return {"success": False, "message": "Customer not found."}

            current_plan = row[0]
            ok, action, reason = validate_subscription_transition(current_plan, target_plan)
            if not ok:
                return {
                    "success": False,
                    "action": action,
                    "message": reason,
                    "current_plan": current_plan,
                    "target_plan": target_plan,
                }

            cur.execute(
                """
                UPDATE customers
                SET subscription_plan = %s
                WHERE id = %s
                RETURNING subscription_plan
                """,
                (target_plan, customer_id),
            )
            updated = cur.fetchone()[0]
        conn.commit()

        return {
            "success": True,
            "action": action,
            "message": f"Subscription updated from {current_plan} to {updated}.",
            "current_plan": current_plan,
            "updated_plan": updated,
        }
    finally:
        conn.close()


def store_conversation_message(
    customer_id: int,
    ticket_id: str,
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO conversation_messages (
                    customer_id,
                    ticket_id,
                    message_role,
                    message_content,
                    metadata
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, customer_id, ticket_id, message_role, message_content, metadata, created_at
                """,
                (customer_id, ticket_id, role, content, Json(metadata or {})),
            )
            row = cur.fetchone()
        conn.commit()
        return dict(row)
    finally:
        conn.close()


def get_recent_conversation_history(
    customer_id: int, limit: int = 20
) -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT message_role, message_content, created_at
                FROM conversation_messages
                WHERE customer_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (customer_id, limit),
            )
            rows = cur.fetchall()

        rows.reverse()
        return [
            {
                "role": row["message_role"],
                "content": row["message_content"],
                "created_at": row["created_at"].isoformat(),
            }
            for row in rows
        ]
    finally:
        conn.close()


def store_support_event(
    customer_id: int,
    ticket_id: str,
    event_type: str,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO support_events (customer_id, ticket_id, event_type, details)
                VALUES (%s, %s, %s, %s)
                RETURNING id, customer_id, ticket_id, event_type, details, created_at
                """,
                (customer_id, ticket_id, event_type, Json(details or {})),
            )
            row = cur.fetchone()
        conn.commit()
        return dict(row)
    finally:
        conn.close()