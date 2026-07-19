import csv
import io
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database.session import get_db
from app.models import models
from app.schemas import schemas
from app.auth import security

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/dashboard-stats", response_model=schemas.DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    today = datetime.date.today()
    start_of_month = today.replace(day=1)
    
    # Today's Sales
    today_sales_query = db.query(func.sum(models.Invoice.grand_total)).filter(
        models.Invoice.invoice_date == today,
        models.Invoice.status != "cancelled"
    ).scalar()
    today_sales = today_sales_query or 0.0
    
    # Monthly Sales
    monthly_sales_query = db.query(func.sum(models.Invoice.grand_total)).filter(
        models.Invoice.invoice_date >= start_of_month,
        models.Invoice.status != "cancelled"
    ).scalar()
    monthly_sales = monthly_sales_query or 0.0
    
    # Invoices count
    invoices_count = db.query(models.Invoice).count()
    
    # Customers count
    customers_count = db.query(models.Customer).count()
    
    # Products count
    products_count = db.query(models.Product).count()
    
    # GST Collected (CGST + SGST + IGST)
    gst_query = db.query(
        func.sum(models.Invoice.cgst + models.Invoice.sgst + models.Invoice.igst)
    ).filter(
        models.Invoice.status != "cancelled"
    ).scalar()
    gst_collected = gst_query or 0.0
    
    return {
        "today_sales": round(today_sales, 2),
        "monthly_sales": round(monthly_sales, 2),
        "invoices_count": invoices_count,
        "customers_count": customers_count,
        "products_count": products_count,
        "gst_collected": round(gst_collected, 2)
    }

@router.get("/sales/trend", response_model=List[schemas.DailySales])
def get_sales_trend(
    days: int = Query(30, description="Number of past days to show"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    start_date = datetime.date.today() - datetime.timedelta(days=days)
    
    results = db.query(
        models.Invoice.invoice_date.label("date"),
        func.sum(models.Invoice.grand_total).label("sales"),
        func.count(models.Invoice.id).label("count")
    ).filter(
        models.Invoice.invoice_date >= start_date,
        models.Invoice.status != "cancelled"
    ).group_by(
        models.Invoice.invoice_date
    ).order_by(
        models.Invoice.invoice_date
    ).all()
    
    return [
        {"date": r.date, "sales": round(r.sales or 0.0, 2), "count": r.count}
        for r in results
    ]

@router.get("/sales/monthly", response_model=List[schemas.MonthlySales])
def get_monthly_sales(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # Depending on DB, date parsing might differ. For SQLite & Postgres, func.strftime or func.to_char.
    # To keep it generic, we'll fetch invoices and group in python, or use a general query.
    # Grouping in python is safe across database engines (SQLite/PostgreSQL) for moderate data sizes.
    invoices = db.query(
        models.Invoice.invoice_date,
        models.Invoice.grand_total
    ).filter(
        models.Invoice.status != "cancelled"
    ).all()
    
    monthly_data = {}
    for inv in invoices:
        month_key = inv.invoice_date.strftime("%Y-%m") # e.g. "2026-07"
        if month_key not in monthly_data:
            monthly_data[month_key] = {"sales": 0.0, "count": 0}
        monthly_data[month_key]["sales"] += inv.grand_total
        monthly_data[month_key]["count"] += 1
        
    sorted_months = sorted(monthly_data.keys(), reverse=True)[:12]
    return [
        {
            "month": m,
            "sales": round(monthly_data[m]["sales"], 2),
            "count": monthly_data[m]["count"]
        }
        for m in sorted_months
    ]

@router.get("/sales/customers", response_model=List[schemas.CustomerSales])
def get_customer_sales(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    results = db.query(
        models.Customer.id.label("customer_id"),
        models.Customer.company_name.label("company_name"),
        func.sum(models.Invoice.grand_total).label("sales"),
        func.count(models.Invoice.id).label("count")
    ).join(
        models.Invoice, models.Customer.id == models.Invoice.customer_id
    ).filter(
        models.Invoice.status != "cancelled"
    ).group_by(
        models.Customer.id,
        models.Customer.company_name
    ).order_by(
        desc("sales")
    ).all()
    
    return [
        {
            "customer_id": r.customer_id,
            "company_name": r.company_name,
            "sales": round(r.sales or 0.0, 2),
            "count": r.count
        }
        for r in results
    ]

@router.get("/sales/products", response_model=List[schemas.ProductSales])
def get_product_sales(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    results = db.query(
        models.Product.id.label("product_id"),
        models.Product.product_name.label("product_name"),
        func.sum(models.InvoiceItem.quantity).label("quantity"),
        func.sum(models.InvoiceItem.amount).label("sales")
    ).join(
        models.InvoiceItem, models.Product.id == models.InvoiceItem.product_id
    ).join(
        models.Invoice, models.Invoice.id == models.InvoiceItem.invoice_id
    ).filter(
        models.Invoice.status != "cancelled"
    ).group_by(
        models.Product.id,
        models.Product.product_name
    ).order_by(
        desc("sales")
    ).all()
    
    return [
        {
            "product_id": r.product_id,
            "product_name": r.product_name,
            "quantity": r.quantity or 0.0,
            "sales": round(r.sales or 0.0, 2)
        }
        for r in results
    ]

@router.get("/gst", response_model=List[schemas.GSTReportItem])
def get_gst_report(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    invoices = db.query(models.Invoice).filter(models.Invoice.status != "cancelled").order_by(desc(models.Invoice.invoice_date)).all()
    
    return [
        {
            "invoice_number": inv.invoice_number,
            "invoice_date": inv.invoice_date,
            "customer_name": inv.customer.company_name,
            "gst_number": inv.customer.gst_number,
            "subtotal": inv.subtotal,
            "cgst": inv.cgst,
            "sgst": inv.sgst,
            "igst": inv.igst,
            "grand_total": inv.grand_total
        }
        for inv in invoices
    ]

@router.get("/export-csv")
def export_sales_csv(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    invoices = db.query(models.Invoice).filter(models.Invoice.status != "cancelled").all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write Headers
    writer.writerow([
        "Invoice Number", "Invoice Date", "Customer Name", "Customer GST", 
        "Subtotal (INR)", "CGST (INR)", "SGST (INR)", "IGST (INR)", 
        "Grand Total (INR)", "Status"
    ])
    
    for inv in invoices:
        writer.writerow([
            inv.invoice_number,
            inv.invoice_date.strftime("%Y-%m-%d"),
            inv.customer.company_name,
            inv.customer.gst_number or "N/A",
            inv.subtotal,
            inv.cgst,
            inv.sgst,
            inv.igst,
            inv.grand_total,
            inv.status
        ])
        
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=Sales_GST_Report.csv"}
    )
