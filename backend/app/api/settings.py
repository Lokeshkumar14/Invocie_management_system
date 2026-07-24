from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models import models
from app.schemas import schemas
from app.auth import security

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("/company", response_model=schemas.CompanyDetailsResponse)
def get_company(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    company = db.query(models.CompanyDetails).first()
    if not company:
        # Create standard placeholder company details
        company = models.CompanyDetails(
            company_name="Vibrant Textiles",
            address="456, GIDC Industrial Estate, Surat, Gujarat - 395006",
            gst="24AAAAA0000A1Z5",
            pan="ABCDE1234F",
            state="Gujarat",
            bank_name="State Bank of India",
            account_number="30001234567",
            ifsc="SBIN0001234",
            logo=""
        )
        db.add(company)
        db.commit()
        db.refresh(company)
    return company

@router.put("/company", response_model=schemas.CompanyDetailsResponse)
def update_company(
    company_data: schemas.CompanyDetailsCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    company = db.query(models.CompanyDetails).first()
    if not company:
        company = models.CompanyDetails(**company_data.dict())
        db.add(company)
    else:
        for key, value in company_data.dict().items():
            setattr(company, key, value)
            
    db.commit()
    db.refresh(company)
    return company
