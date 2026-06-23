import psycopg2


def get_connection():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="halley's",
        dbname="customer_support"
    )