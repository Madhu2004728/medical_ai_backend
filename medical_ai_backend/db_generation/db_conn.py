import psycopg2

DB_CONFIG = {
"dbname": "lit_db",
"user": "postgres",
"password": "123456",
"host": "localhost",
"port": "5432"
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)
