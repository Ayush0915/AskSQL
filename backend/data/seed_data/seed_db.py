import os
import pandas as pd
from sqlalchemy import create_engine, text

# Database connection settings
# Can be overridden via DATABASE_ADMIN_URL env var (e.g. in Docker)
DATABASE_ADMIN_URL = os.getenv("DATABASE_ADMIN_URL", "postgresql://postgres@localhost:5432/asksql")

# Derive standard postgres default URL for creating the DB
# E.g. "postgresql://postgres@localhost:5432/asksql" -> "postgresql://postgres@localhost:5432/postgres"
if DATABASE_ADMIN_URL.endswith("/asksql"):
    DB_URL_DEFAULT = DATABASE_ADMIN_URL.replace("/asksql", "/postgres")
else:
    # Fallback to defaults
    DB_URL_DEFAULT = "postgresql://postgres@localhost:5432/postgres"

DB_URL_APP = DATABASE_ADMIN_URL

READONLY_USER = "asksql_readonly"
READONLY_PASS = "readonly_password"  # Can be changed later/configured in .env

CSV_TABLE_MAPPING = {
    "olist_customers_dataset.csv": "customers",
    "olist_orders_dataset.csv": "orders",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_order_reviews_dataset.csv": "order_reviews",
    "olist_products_dataset.csv": "products",
    "olist_sellers_dataset.csv": "sellers",
    "product_category_name_translation.csv": "category_name_translation"
}

DATETIME_COLUMNS = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ],
    "order_items": [
        "shipping_limit_date"
    ],
    "order_reviews": [
        "review_creation_date",
        "review_answer_timestamp"
    ]
}

def create_database():
    print("Checking if asksql database exists...")
    engine = create_engine(DB_URL_DEFAULT, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = 'asksql'"))
        exists = result.scalar()
        if not exists:
            print("Creating database asksql...")
            conn.execute(text("CREATE DATABASE asksql"))
        else:
            print("Database asksql already exists.")

def setup_readonly_role():
    print(f"Setting up read-only role: {READONLY_USER}...")
    engine = create_engine(DB_URL_APP, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        # Check if role exists
        role_exists = conn.execute(
            text("SELECT 1 FROM pg_roles WHERE rolname = :role"), 
            {"role": READONLY_USER}
        ).scalar()
        
        if not role_exists:
            print(f"Creating role {READONLY_USER}...")
            conn.execute(text(f"CREATE ROLE {READONLY_USER} WITH LOGIN PASSWORD '{READONLY_PASS}'"))
        else:
            print(f"Role {READONLY_USER} already exists. Updating password...")
            conn.execute(text(f"ALTER ROLE {READONLY_USER} WITH PASSWORD '{READONLY_PASS}'"))
        
        # Grant permissions
        conn.execute(text(f"GRANT CONNECT ON DATABASE asksql TO {READONLY_USER}"))
        conn.execute(text(f"GRANT USAGE ON SCHEMA public TO {READONLY_USER}"))
        print("Read-only role setup completed.")

def grant_readonly_select():
    print(f"Granting SELECT permissions on all tables to {READONLY_USER}...")
    engine = create_engine(DB_URL_APP, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        conn.execute(text(f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {READONLY_USER}"))
        conn.execute(text(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO {READONLY_USER}"))
    print("Permissions granted.")

def load_data():
    seed_data_dir = os.path.dirname(os.path.abspath(__file__))
    engine = create_engine(DB_URL_APP)
    
    for csv_file, table_name in CSV_TABLE_MAPPING.items():
        csv_path = os.path.join(seed_data_dir, csv_file)
        if not os.path.exists(csv_path):
            print(f"Warning: {csv_file} not found. Skipping.")
            continue
            
        print(f"Loading {csv_file} into table '{table_name}'...")
        # Read with pandas
        df = pd.read_csv(csv_path)
        
        # Convert timestamp columns to datetime objects
        if table_name in DATETIME_COLUMNS:
            for col in DATETIME_COLUMNS[table_name]:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Write to PostgreSQL
        # if_exists='replace' will overwrite/create the table
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        print(f"Loaded {len(df)} rows into '{table_name}'.")

def main():
    try:
        create_database()
        setup_readonly_role()
        load_data()
        grant_readonly_select()
        print("Database seeding completed successfully!")
    except Exception as e:
        print(f"Error seeding database: {e}")

if __name__ == "__main__":
    main()
