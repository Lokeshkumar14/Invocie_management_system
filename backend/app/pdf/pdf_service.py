import base64
import binascii
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from app.models import models


def get_company_logo(logo: str | None):
    """Return a scaled logo flowable, or None when no valid image was saved."""
    if not logo:
        return None

    try:
        image_data = logo.split(",", 1)[1] if logo.startswith("data:image/") else logo
        image_stream = io.BytesIO(base64.b64decode(image_data, validate=True))
        width, height = ImageReader(image_stream).getSize()
        if width <= 0 or height <= 0:
            return None

        max_width, max_height = 70, 55
        scale = min(max_width / width, max_height / height)
        image_stream.seek(0)
        return Image(image_stream, width=width * scale, height=height * scale)
    except (ValueError, binascii.Error, OSError):
        return None


def generate_invoice_pdf(invoice: models.Invoice, company: models.CompanyDetails) -> io.BytesIO:
    buffer = io.BytesIO()
    
    # Page setup
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1A365D') # Deep Navy
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#2D3748')
    )
    
    normal_bold = ParagraphStyle(
        'NormalBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12
    )
    
    normal_text = ParagraphStyle(
        'NormalText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#4A5568')
    )
    
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=1 # Centered
    )
    
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11
    )
    
    table_cell_center = ParagraphStyle(
        'TableCellCenter',
        parent=table_cell_style,
        alignment=1
    )
    
    table_cell_right = ParagraphStyle(
        'TableCellRight',
        parent=table_cell_style,
        alignment=2
    )

    # 1. HEADER SECTION (Two Columns: Company Info & Invoice Title)
    company_name = company.company_name if company else "Your Textile Company"
    company_address = company.address if company else "123, Textile Market, Ring Road, Surat"
    company_gst = company.gst if company else "24AAAAA0000A1Z5"
    company_pan = company.pan if company else "ABCDE1234F"

    company_info = [
        Paragraph(company_name, title_style),
        Spacer(1, 4),
        Paragraph(f"<b>Address:</b> {company_address}", normal_text),
        Paragraph(f"<b>GSTIN:</b> {company_gst} | <b>PAN:</b> {company_pan}", normal_text)
    ]

    logo = get_company_logo(company.logo if company else None)
    header_left = company_info if not logo else Table(
        [[logo, company_info]],
        colWidths=[80, 240],
        style=[
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ],
    )
    
    header_right = [
        Paragraph("TAX INVOICE", ParagraphStyle('TaxInvoice', parent=title_style, alignment=2, fontSize=22, textColor=colors.HexColor('#2B6CB0'))),
        Spacer(1, 6),
        Paragraph(f"<b>Invoice No:</b> {invoice.invoice_number}", ParagraphStyle('RightBold', parent=normal_bold, alignment=2)),
        Paragraph(f"<b>Date:</b> {invoice.invoice_date.strftime('%d-%b-%Y')}", ParagraphStyle('RightText', parent=normal_text, alignment=2))
    ]
    
    header_table_data = [[header_left, header_right]]
    # Document width is 612 - 72 = 540
    header_table = Table(header_table_data, colWidths=[320, 220])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 15))
    
    # 2. DETAILS SECTION (Customer Details & Shipping / Metadata)
    cust = invoice.customer
    customer_info = [
        Paragraph("<b>Billed To:</b>", subtitle_style),
        Spacer(1, 4),
        Paragraph(f"<b>{cust.company_name}</b>", normal_bold),
        Paragraph(f"Contact: {cust.contact_person or ''}", normal_text),
        Paragraph(f"Address: {cust.address or ''}", normal_text),
        Paragraph(f"GSTIN: {cust.gst_number or 'N/A'} | PAN: {cust.pan_number or 'N/A'}", normal_text),
        Paragraph(f"Mobile: {cust.mobile or ''}", normal_text),
    ]
    
    invoice_meta = [
        Paragraph("<b>Shipping / Dispatch Details:</b>", subtitle_style),
        Spacer(1, 4),
        Paragraph(f"<b>Shipping Address:</b> {cust.shipping_address or cust.address or 'N/A'}", normal_text),
        Spacer(1, 4),
        Paragraph(f"<b>Transport:</b> {invoice.transport or 'N/A'}", normal_text),
        Paragraph(f"<b>Sale Order:</b> {invoice.sale_order or 'N/A'}", normal_text),
        Paragraph(f"<b>Payment Terms:</b> {invoice.payment_terms or 'N/A'}", normal_text),
    ]
    
    details_table_data = [[customer_info, invoice_meta]]
    details_table = Table(details_table_data, colWidths=[270, 270])
    details_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    
    story.append(details_table)
    story.append(Spacer(1, 15))
    
    # 3. ITEMS TABLE
    # Columns: S.No, Product, HSN, Color, Qty, Unit, Rate, GST%, Total
    items_header = [
        Paragraph("S.No", table_header_style),
        Paragraph("Product", table_header_style),
        Paragraph("HSN", table_header_style),
        Paragraph("Color", table_header_style),
        Paragraph("Qty", table_header_style),
        Paragraph("Unit", table_header_style),
        Paragraph("Rate", table_header_style),
        Paragraph("GST %", table_header_style),
        Paragraph("Amount", table_header_style)
    ]
    
    items_data = [items_header]
    
    for idx, item in enumerate(invoice.items, 1):
        prod = item.product
        items_data.append([
            Paragraph(str(idx), table_cell_center),
            Paragraph(prod.product_name, table_cell_style),
            Paragraph(prod.hsn or "-", table_cell_center),
            Paragraph(prod.color or "-", table_cell_center),
            Paragraph(f"{item.quantity:.2f}", table_cell_right),
            Paragraph(prod.unit or "Mtrs", table_cell_center),
            Paragraph(f"₹{item.rate:.2f}", table_cell_right),
            Paragraph(f"{prod.gst_percentage:.1f}%", table_cell_center),
            Paragraph(f"₹{item.amount:.2f}", table_cell_right)
        ])
        
    items_table = Table(items_data, colWidths=[30, 140, 50, 50, 45, 45, 55, 45, 80])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A365D')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 10))
    
    # 4. SUMMARIZATION & FINANCIAL DETAILS (Bank + Totals)
    bank_name = company.bank_name if company else "N/A"
    ac_no = company.account_number if company else "N/A"
    ifsc = company.ifsc if company else "N/A"
    
    bank_details_para = [
        Paragraph("<b>Bank Transfer Information</b>", subtitle_style),
        Spacer(1, 4),
        Paragraph(f"<b>Bank Name:</b> {bank_name}", normal_text),
        Paragraph(f"<b>A/c Number:</b> {ac_no}", normal_text),
        Paragraph(f"<b>IFSC Code:</b> {ifsc}", normal_text),
        Spacer(1, 8),
        Paragraph(f"<b>Remarks:</b> {invoice.remarks or 'Thank you for your business!'}", normal_text)
    ]
    
    # Totals table mapping
    totals_rows = [
        [Paragraph("<b>Subtotal:</b>", normal_text), Paragraph(f"₹{invoice.subtotal:.2f}", table_cell_right)]
    ]
    
    if invoice.cgst > 0:
        totals_rows.append([Paragraph("<b>CGST:</b>", normal_text), Paragraph(f"₹{invoice.cgst:.2f}", table_cell_right)])
    if invoice.sgst > 0:
        totals_rows.append([Paragraph("<b>SGST:</b>", normal_text), Paragraph(f"₹{invoice.sgst:.2f}", table_cell_right)])
    if invoice.igst > 0:
        totals_rows.append([Paragraph("<b>IGST:</b>", normal_text), Paragraph(f"₹{invoice.igst:.2f}", table_cell_right)])
        
    totals_rows.append([
        Paragraph("<b>Grand Total:</b>", ParagraphStyle('GrandBold', parent=normal_bold, fontSize=11, textColor=colors.HexColor('#1A365D'))),
        Paragraph(f"<b>₹{invoice.grand_total:.2f}</b>", ParagraphStyle('GrandRight', parent=table_cell_right, fontSize=11, fontName='Helvetica-Bold'))
    ])
    
    totals_table = Table(totals_rows, colWidths=[110, 110])
    totals_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    
    financials_data = [[bank_details_para, totals_table]]
    financials_table = Table(financials_data, colWidths=[320, 220])
    financials_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    # Wrap amount in words & signature area in KeepTogether to avoid orphans
    signature_section = []
    signature_section.append(Spacer(1, 10))
    signature_section.append(Paragraph(f"<b>Amount in Words:</b> <i>{invoice.amount_words}</i>", normal_text))
    signature_section.append(Spacer(1, 20))
    
    # Authorized signatory block
    sig_left = [
        Paragraph("<b>Terms & Conditions:</b>", normal_bold),
        Paragraph("1. Goods once sold will not be taken back.", normal_text),
        Paragraph("2. Subject to Surat jurisdiction.", normal_text),
    ]
    sig_right = [
        Paragraph(f"For <b>{company_name}</b>", ParagraphStyle('CenterBold', parent=normal_bold, alignment=1)),
        Spacer(1, 40),
        Paragraph("Authorized Signatory", ParagraphStyle('CenterText', parent=normal_text, alignment=1))
    ]
    sig_table = Table([[sig_left, sig_right]], colWidths=[300, 240])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    signature_section.append(sig_table)
    
    story.append(financials_table)
    story.append(KeepTogether(signature_section))
    
    # Build Document
    doc.build(story)
    
    buffer.seek(0)
    return buffer
