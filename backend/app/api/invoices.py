import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import desc
from decimal import Decimal, ROUND_HALF_UP
from app.database.session import get_db
from app.models import models
from app.schemas import schemas
from app.auth import security
from app.utils.number_to_words import num_to_words
from app.pdf.pdf_service import generate_invoice_pdf

router = APIRouter(prefix="/invoice", tags=["invoices"])

def get_company_details(db: Session) -> models.CompanyDetails:
    # Get the first record of company details
    company = db.query(models.CompanyDetails).first()
    if not company:
        # Return a temporary mock object to avoid crashes, or create default
        default_company = models.CompanyDetails(
            company_name="Vibrant Textiles",
            address="456, GIDC Industrial Estate, Surat, Gujarat - 395006",
            gst="24AAAAA0000A1Z5",
            pan="ABCDE1234F",
            bank_name="State Bank of India",
            account_number="30001234567",
            ifsc="SBIN0001234",
            logo=""
        )
        db.add(default_company)
        db.commit()
        db.refresh(default_company)
        return default_company
    return company

@router.get("", response_model=List[schemas.InvoiceResponse])
def read_invoices(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # Retrieve all invoices, ordering by date and ID descending
    return db.query(models.Invoice).order_by(desc(models.Invoice.invoice_date), desc(models.Invoice.id)).all()

@router.get("/{invoice_id}", response_model=schemas.InvoiceResponse)
def read_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.post("", response_model=schemas.InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    invoice_data: schemas.InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    invoice_type = (invoice_data.invoice_type or "tax_invoice").lower()
    if invoice_type not in {"tax_invoice", "job_work"}:
        raise HTTPException(status_code=422, detail="Invoice type must be tax_invoice or job_work")

    # 1. Fetch Customer
    customer = db.query(models.Customer).filter(models.Customer.id == invoice_data.customer_id).first()
    if not customer:
        raise HTTPException(status_code=400, detail="Customer not found")
        
    # 2. Fetch Company Details to compare states
    company = get_company_details(db)
    
    # Clean and compare states
    company_state = (company.address or "Maharashtra").split(",")[-1].strip().lower()
    # Or split by pin, or parse state from field directly if we add one.
    # To make this robust, let's look at DEFAULT_COMPANY_STATE env or standard state field
    company_state_configured = os.getenv("DEFAULT_COMPANY_STATE", "Maharashtra").strip().lower()
    
    customer_state = (customer.state or "").strip().lower()
    is_same_state = (customer_state == company_state_configured)
    
    # 3. Handle Auto Invoice Number
    invoice_num = invoice_data.invoice_number
    if not invoice_num or invoice_num.upper() == "AUTO":
        # Find latest invoice to increment number
        latest_inv = db.query(models.Invoice).order_by(desc(models.Invoice.id)).first()
        next_id = (latest_inv.id + 1) if latest_inv else 1
        prefix = "JWI" if invoice_type == "job_work" else "INV"
        invoice_num = f"{prefix}-{invoice_data.invoice_date.year}-{next_id:04d}"

    # Verify invoice number is unique
    existing_inv = db.query(models.Invoice).filter(models.Invoice.invoice_number == invoice_num).first()
    if existing_inv:
        raise HTTPException(status_code=400, detail=f"Invoice number '{invoice_num}' already exists")

    # 4. Create Invoice instance skeleton
    db_invoice = models.Invoice(
        invoice_number=invoice_num,
        invoice_date=invoice_data.invoice_date,
        customer_id=invoice_data.customer_id,
        invoice_type=invoice_type,
        transport=invoice_data.transport,
        sale_order=invoice_data.sale_order,
        payment_terms=invoice_data.payment_terms,
        challan_number=invoice_data.challan_number,
        job_work_reference=invoice_data.job_work_reference,
        job_work_description=invoice_data.job_work_description,
        remarks=invoice_data.remarks,
        status=invoice_data.status or "unpaid",
        subtotal=0.0,
        cgst=0.0,
        sgst=0.0,
        igst=0.0,
        round_off=0.0,
        grand_total=0.0,
        amount_words=""
    )
    
    # Save skeleton to get ID
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)

    # 5. Populate and Calculate items
    subtotal = 0.0
    total_gst = 0.0
    
    for item_data in invoice_data.items:
        product = db.query(models.Product).filter(models.Product.id == item_data.product_id).first()
        if not product:
            # Delete skeleton to clean up
            db.delete(db_invoice)
            db.commit()
            raise HTTPException(status_code=400, detail=f"Product with ID {item_data.product_id} not found")
            
        qty = item_data.quantity
        rate = item_data.rate
        basic_amount = qty * rate
        
        # Calculate GST amount for this product item
        gst_percent = product.gst_percentage or 0.0
        item_gst = basic_amount * (gst_percent / 100.0)
        
        db_item = models.InvoiceItem(
            invoice_id=db_invoice.id,
            product_id=item_data.product_id,
            quantity=qty,
            rate=rate,
            dc_number=item_data.dc_number,
            dc_date=item_data.dc_date,
            dia=item_data.dia,
            rolls=item_data.rolls,
            gst=item_gst,
            amount=basic_amount
        )
        db.add(db_item)
        
        subtotal += basic_amount
        total_gst += item_gst

    # 6. Apply GST Engine logic
    if is_same_state:
        cgst = total_gst / 2.0
        sgst = total_gst / 2.0
        igst = 0.0
    else:
        cgst = 0.0
        sgst = 0.0
        igst = total_gst

    taxable_total = subtotal + cgst + sgst + igst
    # Indian invoices conventionally round the payable amount to the nearest rupee.
    # ROUND_HALF_UP avoids Python's banker's rounding at exactly 50 paise.
    grand_total = float(Decimal(str(taxable_total)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    round_off = grand_total - taxable_total
    amount_words = num_to_words(grand_total)

    # Update Invoice tallies
    db_invoice.subtotal = round(subtotal, 2)
    db_invoice.cgst = round(cgst, 2)
    db_invoice.sgst = round(sgst, 2)
    db_invoice.igst = round(igst, 2)
    db_invoice.round_off = round(round_off, 2)
    db_invoice.grand_total = grand_total
    db_invoice.amount_words = amount_words

    db.commit()
    db.refresh(db_invoice)
    return db_invoice

@router.delete("/{invoice_id}")
def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    db.delete(invoice)
    db.commit()
    return {"detail": "Invoice deleted successfully"}

@router.get(
    "/{invoice_id}/pdf",
    response_class=Response,
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Invoice PDF",
        }
    },
)
def get_pdf(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    company = get_company_details(db)
    pdf_buffer = generate_invoice_pdf(invoice, company)
    
    filename = f"Invoice_{invoice.invoice_number}.pdf"
    
    pdf_content = pdf_buffer.getvalue()

    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_content)),
        },
    )
