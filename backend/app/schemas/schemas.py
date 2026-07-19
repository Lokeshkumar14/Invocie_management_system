from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import date, datetime

# Token & Auth
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str
    role: Optional[str] = "admin"

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

# Customer Schemas
class CustomerBase(BaseModel):
    company_name: str
    contact_person: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[EmailStr] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    shipping_address: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[EmailStr] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    shipping_address: Optional[str] = None

class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Product Schemas
class ProductBase(BaseModel):
    product_name: str
    hsn: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    color: Optional[str] = None
    gst_percentage: float = 0.0
    price: float = 0.0

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    hsn: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    color: Optional[str] = None
    gst_percentage: Optional[float] = None
    price: Optional[float] = None

class ProductResponse(ProductBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Company Details Schemas
class CompanyDetailsBase(BaseModel):
    company_name: str
    address: Optional[str] = None
    gst: Optional[str] = None
    pan: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc: Optional[str] = None
    logo: Optional[str] = None  # Base64 string or image URL

class CompanyDetailsCreate(CompanyDetailsBase):
    pass

class CompanyDetailsResponse(CompanyDetailsBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Invoice Items
class InvoiceItemBase(BaseModel):
    product_id: int
    quantity: float
    rate: float

class InvoiceItemCreate(InvoiceItemBase):
    pass

class InvoiceItemResponse(BaseModel):
    id: int
    invoice_id: int
    product_id: int
    quantity: float
    rate: float
    gst: float
    amount: float
    product: Optional[ProductResponse] = None

    class Config:
        from_attributes = True

# Invoice
class InvoiceBase(BaseModel):
    invoice_number: str
    invoice_date: date
    customer_id: int
    transport: Optional[str] = None
    sale_order: Optional[str] = None
    payment_terms: Optional[str] = None
    remarks: Optional[str] = None
    status: Optional[str] = "unpaid"

class InvoiceCreate(InvoiceBase):
    items: List[InvoiceItemCreate]

class InvoiceResponse(InvoiceBase):
    id: int
    subtotal: float
    cgst: float
    sgst: float
    igst: float
    grand_total: float
    amount_words: str
    created_at: datetime
    customer: CustomerResponse
    items: List[InvoiceItemResponse]

    class Config:
        from_attributes = True

# Analytics / Report Schemas
class DailySales(BaseModel):
    date: date
    sales: float
    count: int

class MonthlySales(BaseModel):
    month: str
    sales: float
    count: int

class CustomerSales(BaseModel):
    customer_id: int
    company_name: str
    sales: float
    count: int

class ProductSales(BaseModel):
    product_id: int
    product_name: str
    quantity: float
    sales: float

class GSTReportItem(BaseModel):
    invoice_number: str
    invoice_date: date
    customer_name: str
    gst_number: Optional[str] = None
    subtotal: float
    cgst: float
    sgst: float
    igst: float
    grand_total: float

class DashboardStats(BaseModel):
    today_sales: float
    monthly_sales: float
    invoices_count: int
    customers_count: int
    products_count: int
    gst_collected: float
