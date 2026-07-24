import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="admin") # e.g. "admin", "staff"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, nullable=False, index=True)
    contact_person = Column(String)
    mobile = Column(String)
    email = Column(String)
    gst_number = Column(String, index=True)
    pan_number = Column(String)
    address = Column(Text)
    city = Column(String)
    state = Column(String)
    pincode = Column(String)
    shipping_address = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    invoices = relationship("Invoice", back_populates="customer")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, nullable=False, index=True)
    hsn = Column(String)
    description = Column(Text)
    unit = Column(String)  # e.g., "Meters", "Pcs"
    color = Column(String)
    gst_percentage = Column(Float, default=0.0) # e.g., 5.0, 12.0, 18.0
    price = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class CompanyDetails(Base):
    __tablename__ = "company_details"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, nullable=False)
    address = Column(Text)
    gst = Column(String)
    pan = Column(String)
    state = Column(String)  # Company's state for GST (CGST/SGST vs IGST)
    bank_name = Column(String)
    account_number = Column(String)
    ifsc = Column(String)
    logo = Column(String) # Base64 data URI or path
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, unique=True, index=True, nullable=False)
    invoice_date = Column(Date, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    # `tax_invoice` is the normal sales invoice; `job_work` is for processing
    # charges billed against material supplied by the customer.
    invoice_type = Column(String, nullable=False, default="tax_invoice")
    
    # Extra header fields
    transport = Column(String)
    sale_order = Column(String)
    payment_terms = Column(String)
    challan_number = Column(String)
    job_work_reference = Column(String)
    job_work_description = Column(Text)
    
    # Financial fields
    subtotal = Column(Float, default=0.0)
    cgst = Column(Float, default=0.0)
    sgst = Column(Float, default=0.0)
    igst = Column(Float, default=0.0)
    round_off = Column(Float, default=0.0)
    grand_total = Column(Float, default=0.0)
    amount_words = Column(String)
    remarks = Column(Text)
    status = Column(String, default="unpaid") # paid, unpaid, cancelled
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")

class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    rate = Column(Float, nullable=False)
    dc_number = Column(String)
    dc_date = Column(Date)
    dia = Column(String)
    rolls = Column(Float)
    gst = Column(Float, default=0.0)      # GST amount for this item
    amount = Column(Float, nullable=False)   # Total amount for this item (excluding tax or including? usually subtotal, let's store quantity * rate)

    # Relationships
    invoice = relationship("Invoice", back_populates="items")
    product = relationship("Product")
