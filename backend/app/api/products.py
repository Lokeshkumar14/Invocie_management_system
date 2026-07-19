from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database.session import get_db
from app.models import models
from app.schemas import schemas
from app.auth import security

router = APIRouter(prefix="/products", tags=["products"])

@router.get("", response_model=List[schemas.ProductResponse])
def read_products(
    search: Optional[str] = Query(None, description="Search by product name, HSN, or color"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    query = db.query(models.Product)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                models.Product.product_name.like(search_filter),
                models.Product.hsn.like(search_filter),
                models.Product.color.like(search_filter)
            )
        )
    return query.all()

@router.get("/{product_id}", response_model=schemas.ProductResponse)
def read_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("", response_model=schemas.ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.put("/{product_id}", response_model=schemas.ProductResponse)
def update_product(
    product_id: int,
    product_data: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    for key, value in product_data.dict(exclude_unset=True).items():
        setattr(db_product, key, value)
        
    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check if product is in any invoice item
    associated_items = db.query(models.InvoiceItem).filter(models.InvoiceItem.product_id == product_id).first()
    if associated_items:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete product linked to existing invoices."
        )

    db.delete(db_product)
    db.commit()
    return {"detail": "Product deleted successfully"}
