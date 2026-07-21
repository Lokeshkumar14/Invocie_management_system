import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Adjust path to import app correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database.session import Base, get_db
from app.models import models
from app.auth import security

# Separate test DB
TEST_DATABASE_URL = "sqlite://"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    # Seed admin user for tests
    db = TestingSessionLocal()
    hashed_password = security.get_password_hash("admin123")
    user = models.User(username="testadmin", hashed_password=hashed_password, role="admin")
    db.add(user)
    
    # Seed Company Details
    company = models.CompanyDetails(
        company_name="Test Company",
        address="123 Street, Mumbai, Maharashtra - 400001",
        gst="27AAAAA0000A1Z5",
        pan="ABCDE1234F",
        bank_name="Test Bank",
        account_number="123456",
        ifsc="TEST0001"
    )
    db.add(company)
    db.commit()
    db.close()
    yield
    engine.dispose()
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test.db"):
        os.remove("./test.db")

@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

def test_login(client):
    # Test form login
    response = client.post("/api/auth/login", data={"username": "testadmin", "password": "admin123"})
    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    assert json_data["token_type"] == "bearer"

def test_gst_engine_same_state(client):
    # Log in
    login_response = client.post("/api/auth/login", data={"username": "testadmin", "password": "admin123"})
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Create a Customer in Maharashtra (same state as test company details)
    cust_res = client.post("/api/customers", json={
        "company_name": "Maharashtra Client Ltd",
        "state": "Maharashtra",
        "gst_number": "27BBBBB1111B1Z2"
    }, headers=headers)
    assert cust_res.status_code == 201
    cust_id = cust_res.json()["id"]
    
    # 2. Create a Product
    prod_res = client.post("/api/products", json={
        "product_name": "Premium Cotton Silk",
        "gst_percentage": 12.0,
        "price": 500.0,
        "unit": "Meters"
    }, headers=headers)
    assert prod_res.status_code == 201
    prod_id = prod_res.json()["id"]
    
    # 3. Create Invoice
    invoice_payload = {
        "invoice_number": "TEST-SAME-001",
        "invoice_date": "2026-07-19",
        "customer_id": cust_id,
        "items": [
            {
                "product_id": prod_id,
                "quantity": 10.0,
                "rate": 500.0
            }
        ],
        "status": "unpaid"
    }
    inv_res = client.post("/api/invoice", json=invoice_payload, headers=headers)
    assert inv_res.status_code == 201
    inv_data = inv_res.json()
    
    # Assert values:
    # subtotal = 10 * 500 = 5000.0
    # gst (12%) = 5000 * 0.12 = 600.0
    # same state => CGST = 300.0, SGST = 300.0, IGST = 0.0
    # grand_total = 5600.0
    assert inv_data["subtotal"] == 5000.0
    assert inv_data["cgst"] == 300.0
    assert inv_data["sgst"] == 300.0
    assert inv_data["igst"] == 0.0
    assert inv_data["grand_total"] == 5600.0
    assert "Rupees" in inv_data["amount_words"]

def test_gst_engine_different_state(client):
    # Log in
    login_response = client.post("/api/auth/login", data={"username": "testadmin", "password": "admin123"})
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Create a Customer in Gujarat (different state)
    cust_res = client.post("/api/customers", json={
        "company_name": "Gujarat Client Ltd",
        "state": "Gujarat",
        "gst_number": "24CCCCC2222C1Z3"
    }, headers=headers)
    assert cust_res.status_code == 201
    cust_id = cust_res.json()["id"]
    
    # 2. Create a Product
    prod_res = client.post("/api/products", json={
        "product_name": "Cotton Yarn",
        "gst_percentage": 5.0,
        "price": 200.0,
        "unit": "Kgs"
    }, headers=headers)
    assert prod_res.status_code == 201
    prod_id = prod_res.json()["id"]
    
    # 3. Create Invoice
    invoice_payload = {
        "invoice_number": "TEST-DIFF-002",
        "invoice_date": "2026-07-19",
        "customer_id": cust_id,
        "items": [
            {
                "product_id": prod_id,
                "quantity": 50.0,
                "rate": 200.0
            }
        ],
        "status": "unpaid"
    }
    inv_res = client.post("/api/invoice", json=invoice_payload, headers=headers)
    assert inv_res.status_code == 201
    inv_data = inv_res.json()
    
    # Assert values:
    # subtotal = 50 * 200 = 10000.0
    # gst (5%) = 10000 * 0.05 = 500.0
    # different state => CGST = 0.0, SGST = 0.0, IGST = 500.0
    # grand_total = 10500.0
    assert inv_data["subtotal"] == 10000.0
    assert inv_data["cgst"] == 0.0
    assert inv_data["sgst"] == 0.0
    assert inv_data["igst"] == 500.0
    assert inv_data["grand_total"] == 10500.0


def test_job_work_invoice_fields_and_pdf_title(client):
    login_response = client.post("/api/auth/login", data={"username": "testadmin", "password": "admin123"})
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    customer = client.post("/api/customers", json={
        "company_name": "Job Work Client",
        "state": "Maharashtra",
    }, headers=headers).json()
    product = client.post("/api/products", json={
        "product_name": "Dyeing Charges",
        "gst_percentage": 5.0,
        "price": 20.0,
        "unit": "Kgs",
    }, headers=headers).json()

    response = client.post("/api/invoice", json={
        "invoice_number": "JWI-TEST-001",
        "invoice_date": "2026-07-21",
        "invoice_type": "job_work",
        "customer_id": customer["id"],
        "challan_number": "CH-101",
        "job_work_reference": "JW-45",
        "job_work_description": "Dyeing charges for customer supplied fabric",
        "items": [{"product_id": product["id"], "quantity": 100, "rate": 20}],
    }, headers=headers)

    assert response.status_code == 201
    invoice = response.json()
    assert invoice["invoice_type"] == "job_work"
    assert invoice["challan_number"] == "CH-101"
    assert invoice["job_work_reference"] == "JW-45"

    pdf_response = client.get(f"/api/invoice/{invoice['id']}/pdf", headers=headers)
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"].startswith("application/pdf")
    assert pdf_response.content.startswith(b"%PDF")
