import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./invoice.db")

# If sqlite, use check_same_thread=False
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def add_missing_invoice_columns():
    """Apply the small backwards-compatible invoice upgrade for existing installs.

    This project intentionally supports a simple SQLite setup without a separate
    migration command. New databases get these fields through SQLAlchemy's model;
    existing databases receive the nullable columns on application startup.
    """
    expected_columns = {
        "invoice_type": "VARCHAR DEFAULT 'tax_invoice'",
        "challan_number": "VARCHAR",
        "job_work_reference": "VARCHAR",
        "job_work_description": "TEXT",
        "round_off": "FLOAT DEFAULT 0.0",
    }
    inspector = inspect(engine)
    if "invoices" not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("invoices")}
    with engine.begin() as connection:
        for name, sql_type in expected_columns.items():
            if name not in existing_columns:
                connection.execute(text(f"ALTER TABLE invoices ADD COLUMN {name} {sql_type}"))

    item_columns = {
        "dc_number": "VARCHAR",
        "dc_date": "DATE",
        "dia": "VARCHAR",
        "rolls": "FLOAT",
    }
    inspector = inspect(engine)
    existing_item_columns = {column["name"] for column in inspector.get_columns("invoice_items")}
    with engine.begin() as connection:
        for name, sql_type in item_columns.items():
            if name not in existing_item_columns:
                connection.execute(text(f"ALTER TABLE invoice_items ADD COLUMN {name} {sql_type}"))

    # --- company_details table: add `state` column if missing ----------------
    if "company_details" in inspector.get_table_names():
        existing_company_cols = {col["name"] for col in inspector.get_columns("company_details")}
        if "state" not in existing_company_cols:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE company_details ADD COLUMN state VARCHAR"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
