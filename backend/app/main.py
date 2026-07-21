import os
from dotenv import load_dotenv

# Load local development settings before importing modules that read them.
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.session import engine, Base, SessionLocal, add_missing_invoice_columns
from app.models import models
from app.auth import security
from app.api import auth, customers, products, invoices, reports, settings

# Ensure database tables exist
Base.metadata.create_all(bind=engine)
add_missing_invoice_columns()

# Seed the initial administrator only when credentials are supplied through the
# environment. There are intentionally no hard-coded production credentials.
initial_admin_username = os.getenv("INITIAL_ADMIN_USERNAME")
initial_admin_password = os.getenv("INITIAL_ADMIN_PASSWORD")
db = SessionLocal()
try:
    admin_user = (
        db.query(models.User)
        .filter(models.User.username == initial_admin_username)
        .first()
        if initial_admin_username
        else None
    )
    if initial_admin_username and initial_admin_password and not admin_user:
        # Upgrade the legacy development account on the first secure startup.
        legacy_admin = db.query(models.User).filter(models.User.username == "admin").first()
        if legacy_admin and security.verify_password("admin123", legacy_admin.hashed_password):
            legacy_admin.username = initial_admin_username
            legacy_admin.hashed_password = security.get_password_hash(initial_admin_password)
            legacy_admin.role = "admin"
            db.commit()
            print("Migrated the legacy default administrator account")
        else:
            hashed_password = security.get_password_hash(initial_admin_password)
            db_user = models.User(
                username=initial_admin_username,
                hashed_password=hashed_password,
                role="admin"
            )
            db.add(db_user)
            db.commit()
            print("Seeded the administrator account from environment settings")
    elif not initial_admin_username or not initial_admin_password:
        print("INITIAL_ADMIN_USERNAME and INITIAL_ADMIN_PASSWORD are not set; no administrator was seeded")
finally:
    db.close()

app = FastAPI(
    title="Textile Invoice & Billing Management System API",
    version="1.0.0"
)

# CORS origins must be explicitly configured in production. Comma-separated
# values make it possible to allow both a Pages domain and a custom domain.
cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers under /api
app.include_router(auth.router, prefix="/api")
app.include_router(customers.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(invoices.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(settings.router, prefix="/api")

@app.get("/")
def read_root():
    return {"status": "running", "message": "Textile Invoicing API is online"}
