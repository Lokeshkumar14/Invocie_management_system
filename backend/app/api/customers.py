from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database.session import get_db
from app.models import models
from app.schemas import schemas
from app.auth import security

router = APIRouter(prefix="/customers", tags=["customers"])

@router.get("", response_model=List[schemas.CustomerResponse])
def read_customers(
    search: Optional[str] = Query(None, description="Search by company name, contact person, or GST number"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    query = db.query(models.Customer)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                models.Customer.company_name.like(search_filter),
                models.Customer.contact_person.like(search_filter),
                models.Customer.gst_number.like(search_filter)
            )
        )
    return query.all()

@router.get("/{customer_id}", response_model=schemas.CustomerResponse)
def read_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@router.post("", response_model=schemas.CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    customer: schemas.CustomerCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    db_customer = models.Customer(**customer.dict())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

@router.put("/{customer_id}", response_model=schemas.CustomerResponse)
def update_customer(
    customer_id: int,
    customer_data: schemas.CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    db_customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    for key, value in customer_data.dict(exclude_unset=True).items():
        setattr(db_customer, key, value)
        
    db.commit()
    db.refresh(db_customer)
    return db_customer

@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    db_customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Check if customer has associated invoices
    associated_invoices = db.query(models.Invoice).filter(models.Invoice.customer_id == customer_id).first()
    if associated_invoices:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete customer with associated invoices. Delete invoices first."
        )

    db.delete(db_customer)
    db.commit()
    return {"detail": "Customer deleted successfully"}

@router.get("/{customer_id}/history", response_model=List[schemas.InvoiceResponse])
def get_customer_history(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    invoices = db.query(models.Invoice).filter(models.Invoice.customer_id == customer_id).all()
    return invoices
