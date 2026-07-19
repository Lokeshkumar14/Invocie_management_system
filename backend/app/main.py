import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.session import engine, Base, SessionLocal
from app.models import models
from app.auth import security
from app.api import auth, customers, products, invoices, reports, settings

# Ensure database tables exist
Base.metadata.create_all(bind=engine)

# Seed database with initial default user
db = SessionLocal()
try:
    admin_user = db.query(models.User).filter(models.User.username == "admin").first()
    if not admin_user:
        hashed_password = security.get_password_hash("admin123")
        db_user = models.User(
            username="admin",
            hashed_password=hashed_password,
            role="admin"
        )
        db.add(db_user)
        db.commit()
        print("Seeded default admin user: admin/admin123")
finally:
    db.close()

app = FastAPI(
    title="Textile Invoice & Billing Management System API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # During production deployment, specify domain
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
