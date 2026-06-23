import random
from faker import Faker
import psycopg2

fake = Faker()

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="postgres",
    password="halley's",
    dbname="customer_support"
)

cur = conn.cursor()

for _ in range(50):

    cur.execute(
        """
        INSERT INTO customers(
            full_name,
            email,
            subscription_plan,
            account_status
        )
        VALUES (%s,%s,%s,%s)
        RETURNING id
        """,
        (
            fake.name(),
            fake.email(),
            random.choice(
                ["Free", "Premium", "Enterprise"]
            ),
            random.choice(
                ["Active", "Suspended"]
            )
        )
    )

    customer_id = cur.fetchone()[0]

    for _ in range(random.randint(1, 5)):

        cur.execute(
            """
            INSERT INTO orders(
                customer_id,
                product_name,
                order_status,
                total
            )
            VALUES (%s,%s,%s,%s)
            """,
            (
                customer_id,
                random.choice([
                    "Laptop",
                    "Keyboard",
                    "Mouse",
                    "Monitor"
                ]),
                random.choice([
                    "Delivered",
                    "Pending",
                    "Cancelled"
                ]),
                random.randint(20, 1000)
            )
        )

conn.commit()
cur.close()
conn.close()