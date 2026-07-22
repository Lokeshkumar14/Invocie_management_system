"""
Invoice PDF generator.

Produces two layouts from the same `Invoice` / `CompanyDetails` models:

- `generate_job_work_invoice_pdf`  -> compact DC-wise job-work invoice
- `generate_invoice_pdf`           -> standard tax invoice (routes to the
                                      job-work layout automatically when
                                      `invoice.invoice_type == "job_work"`)

Both layouts share the same brand palette, currency formatting, and
page-numbering footer so the output is consistent regardless of which
template is used.
"""

from __future__ import annotations

import base64
import binascii
import io
from collections import defaultdict

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models import models

# --------------------------------------------------------------------------
# Brand palette - shared across both invoice layouts for a consistent look
# --------------------------------------------------------------------------
NAVY = colors.HexColor("#1A365D")
ACCENT_BLUE = colors.HexColor("#2B6CB0")
SLATE = colors.HexColor("#4A5568")
BORDER_GREY = colors.HexColor("#CBD5E0")
LIGHT_BLUE_BG = colors.HexColor("#EAF4FC")
ZEBRA_ROW = colors.HexColor("#F7FAFC")
WHITE = colors.white

LOGO_MAX_WIDTH = 70
LOGO_MAX_HEIGHT = 55


# --------------------------------------------------------------------------
# Currency / number formatting
#
# ReportLab's built-in Helvetica font does not include the Unicode rupee
# glyph (Rs symbol). Rendering it directly produces a solid black box on
# the PDF, so amounts are shown as "Rs. 1,23,456.00" using the Indian
# digit-grouping convention instead.
# --------------------------------------------------------------------------
def format_amount(value) -> str:
    """Format a number with Indian-style digit grouping, e.g. 1,23,456.00."""
    try:
        value = float(value or 0)
    except (TypeError, ValueError):
        value = 0.0

    negative = value < 0
    whole, _, frac = f"{abs(value):.2f}".partition(".")

    if len(whole) > 3:
        last_three = whole[-3:]
        remainder = whole[:-3]
        groups = []
        while len(remainder) > 2:
            groups.insert(0, remainder[-2:])
            remainder = remainder[:-2]
        if remainder:
            groups.insert(0, remainder)
        whole = ",".join(groups + [last_three])

    formatted = f"{whole}.{frac}"
    return f"-{formatted}" if negative else formatted


def money(value) -> str:
    """Currency-labelled, comma-grouped amount safe for ReportLab base fonts."""
    return f"Rs. {format_amount(value)}"


def qty(value, decimals: int = 2) -> str:
    """Format a plain (non-currency) quantity, tolerating None."""
    try:
        return f"{float(value or 0):.{decimals}f}"
    except (TypeError, ValueError):
        return "-"


def text_or_dash(value) -> str:
    return str(value) if value not in (None, "") else "-"


def tax_breakup_rows(invoice: models.Invoice) -> list[tuple[str, float]]:
    """Return GST labels and amounts grouped by product rate and taxable value."""
    taxable_by_rate = defaultdict(float)
    for item in invoice.items or []:
        rate = float(getattr(item.product, "gst_percentage", 0) or 0)
        taxable_by_rate[rate] += float(item.amount or 0)

    is_interstate = bool(invoice.igst)
    rows = []
    for gst_rate, taxable_value in sorted(taxable_by_rate.items()):
        if not gst_rate:
            continue
        if is_interstate:
            rows.append((f"IGST {gst_rate:g}% on {format_amount(taxable_value)}", taxable_value * gst_rate / 100))
        else:
            half_rate = gst_rate / 2
            tax_amount = taxable_value * half_rate / 100
            rows.extend([
                (f"CGST {half_rate:g}% on {format_amount(taxable_value)}", tax_amount),
                (f"SGST {half_rate:g}% on {format_amount(taxable_value)}", tax_amount),
            ])

    # Preserve a useful breakdown for older invoices whose item/product data is incomplete.
    if not rows:
        if is_interstate:
            rows.append(("IGST", invoice.igst))
        else:
            rows.extend([
                ("CGST", invoice.cgst),
                ("SGST", invoice.sgst),
            ])
    return rows


# --------------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------------
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

        scale = min(LOGO_MAX_WIDTH / width, LOGO_MAX_HEIGHT / height)
        image_stream.seek(0)
        return Image(image_stream, width=width * scale, height=height * scale)
    except (ValueError, binascii.Error, OSError):
        return None


class _NumberedCanvas(pdf_canvas.Canvas):
    """Canvas that stamps a 'Page X of Y' footer once the full page count
    is known, so multi-page invoices (long item lists) paginate cleanly."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states: list[dict] = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_page_number(total_pages)
            super().showPage()
        super().save()

    def _draw_page_number(self, total_pages: int):
        if total_pages <= 1:
            return  # keep single-page invoices free of clutter
        self.setFont("Helvetica", 7.5)
        self.setFillColor(SLATE)
        page_width = self._pagesize[0]
        self.drawRightString(
            page_width - 22, 12, f"Page {self._pageNumber} of {total_pages}"
        )


def _build_shared_styles() -> dict[str, ParagraphStyle]:
    """Central style sheet reused by both invoice layouts to avoid drift
    between the two templates."""
    base = getSampleStyleSheet()
    styles = {
        "tiny": ParagraphStyle(
            "Tiny", parent=base["Normal"], fontName="Helvetica", fontSize=6.6, leading=8.4
        ),
    }
    styles["small"] = ParagraphStyle(
        "Small", parent=styles["tiny"], fontSize=7.5, leading=9.5
    )
    styles["bold_small"] = ParagraphStyle(
        "BoldSmall", parent=styles["small"], fontName="Helvetica-Bold"
    )
    styles["centre"] = ParagraphStyle(
        "Centre", parent=styles["small"], alignment=1
    )
    styles["right"] = ParagraphStyle(
        "Right", parent=styles["small"], alignment=2
    )
    styles["body"] = ParagraphStyle(
        "Body", parent=base["Normal"], fontName="Helvetica", fontSize=9,
        leading=12, textColor=SLATE,
    )
    styles["body_bold"] = ParagraphStyle(
        "BodyBold", parent=styles["body"], fontName="Helvetica-Bold", textColor=colors.black,
    )
    styles["subtitle"] = ParagraphStyle(
        "Subtitle", parent=base["Normal"], fontName="Helvetica-Bold",
        fontSize=12, leading=16, textColor=NAVY,
    )
    styles["title"] = ParagraphStyle(
        "Title", parent=base["Normal"], fontName="Helvetica-Bold",
        fontSize=20, leading=24, textColor=NAVY,
    )
    styles["table_header"] = ParagraphStyle(
        "TableHeader", parent=base["Normal"], fontName="Helvetica-Bold",
        fontSize=8, leading=10, textColor=WHITE, alignment=1,
    )
    styles["cell"] = ParagraphStyle(
        "Cell", parent=base["Normal"], fontName="Helvetica", fontSize=8.5, leading=11,
    )
    styles["cell_centre"] = ParagraphStyle(
        "CellCentre", parent=styles["cell"], alignment=1
    )
    styles["cell_right"] = ParagraphStyle(
        "CellRight", parent=styles["cell"], alignment=2
    )
    return styles


# ==========================================================================
# Job-work invoice (compact, DC-wise layout)
# ==========================================================================
def generate_job_work_invoice_pdf(invoice: models.Invoice, company: models.CompanyDetails) -> io.BytesIO:
    """Render the compact DC-wise job-work invoice layout used by textile units."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=22, rightMargin=22, topMargin=18, bottomMargin=24,
        title=f"Job Work Invoice {getattr(invoice, 'invoice_number', '')}".strip(),
    )
    s = _build_shared_styles()
    job_line = colors.HexColor("#8CC4EB")
    job_fill = colors.HexColor("#EAF6FF")
    job_soft_fill = colors.HexColor("#F7FBFF")
    job_text = colors.HexColor("#1C527D")

    company_name = company.company_name if company else "Your Company Name"
    logo = get_company_logo(company.logo if company else None)

    # --- Header: logo + company block, plus invoice number/date box -------
    company_block = [
        Paragraph(f"<b>{company_name.upper()}</b>",
                  ParagraphStyle("JobCompany", parent=s["bold_small"], fontSize=18, leading=21,
                                 textColor=job_text, alignment=1)),
        Paragraph(text_or_dash(company and company.address) if company else "", ParagraphStyle("JobAddress", parent=s["centre"], fontSize=9.5, leading=12)),
        Paragraph(f"GST: {text_or_dash(company and company.gst) if company else '-'}   "
                  f"PAN: {text_or_dash(company and company.pan) if company else '-'}", s["centre"]),
    ]
    header_left = (
        Table([[logo, company_block]], colWidths=[80, 305], style=[
            ("VALIGN", (0, 0), (0, 0), "MIDDLE"), ("VALIGN", (1, 0), (1, 0), "MIDDLE"),
            ("ALIGN", (0, 0), (0, 0), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
        if logo else company_block
    )

    invoice_box = [
        [Paragraph("<b>JOB WORK INVOICE</b>",
                   ParagraphStyle("JobTitle", parent=s["centre"], fontSize=12, textColor=job_text)), ""],
        [Paragraph("<b>INVOICE NO.</b>", ParagraphStyle("JobNoLabel", parent=s["bold_small"], fontSize=7.5, textColor=job_text)), Paragraph(text_or_dash(invoice.invoice_number), ParagraphStyle("JobNoValue", parent=s["right"], fontSize=8.5, fontName="Helvetica-Bold"))],
        [Paragraph("<b>INVOICE DATE</b>", ParagraphStyle("JobDateLabel", parent=s["bold_small"], fontSize=7.5, textColor=job_text)),
         Paragraph(invoice.invoice_date.strftime("%d/%m/%Y") if invoice.invoice_date else "-", ParagraphStyle("JobDateValue", parent=s["right"], fontSize=8.5, fontName="Helvetica-Bold"))],
    ]
    invoice_table = Table(invoice_box, colWidths=[48, 104])
    invoice_table.setStyle(TableStyle([
        ("SPAN", (0, 0), (1, 0)), ("BACKGROUND", (0, 0), (1, 0), job_fill),
        ("GRID", (0, 0), (-1, -1), 0.5, job_line), ("BACKGROUND", (0, 1), (0, -1), job_soft_fill),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    header = Table([[header_left, invoice_table]], colWidths=[385, 152])
    header.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, job_line), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBEFORE", (1, 0), (1, -1), 0.8, job_line), ("BACKGROUND", (0, 0), (0, 0), job_soft_fill),
        # The nested cells already control their own spacing. Zero outer padding
        # keeps the invoice number/date panel exactly inside the 537pt document grid.
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    # --- Customer + job details --------------------------------------------
    customer = invoice.customer
    customer_lines = [
        Paragraph("<b>To M/S</b>", ParagraphStyle("BillTo", parent=s["bold_small"], fontSize=8, textColor=job_text)),
        Paragraph(f"<b>{customer.company_name}</b>", ParagraphStyle("CustomerName", parent=s["bold_small"], fontSize=11, leading=13, textColor=job_text)),
        Paragraph(text_or_dash(customer.address) if customer.address else "", ParagraphStyle("CustomerAddress", parent=s["tiny"], fontSize=8.5, leading=10.5)),
        Paragraph(f"<b>GSTIN:</b> {text_or_dash(customer.gst_number)}", ParagraphStyle("CustomerGst", parent=s["tiny"], fontSize=8.2)),
    ]
    # Keep the three job-detail fields visually distinct without adding lines
    # through the "Bill To" panel on the left.
    job_details = Table([
        [Paragraph(f"<b>Party DC No:</b> {text_or_dash(invoice.challan_number)}", s["small"])],
        [Paragraph(f"<b>Job Ref:</b> {text_or_dash(invoice.job_work_reference)}", s["small"])],
        [Paragraph(f"<b>Work:</b> {text_or_dash(invoice.job_work_description)}", s["small"])],
    ], colWidths=[182])
    job_details.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (0, 1), 0.5, job_line),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    details = Table([[customer_lines, job_details]], colWidths=[355, 182])
    details.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.7, job_line), ("LINEBEFORE", (1, 0), (1, -1), 0.5, job_line),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        # Let the nested job-details table reach the full width of its panel,
        # while retaining the existing padding in the customer panel.
        ("LEFTPADDING", (1, 0), (1, 0), 0), ("RIGHTPADDING", (1, 0), (1, 0), 0),
        ("TOPPADDING", (1, 0), (1, 0), 0), ("BOTTOMPADDING", (1, 0), (1, 0), 0),
        ("BACKGROUND", (0, 0), (-1, -1), job_soft_fill),
    ]))

    # --- Items table ---------------------------------------------------------
    headings = ["S.No", "DC No.", "DC Date", "Fabric", "Dia", "Rolls", "Weight", "Rate", "Amount"]
    rows = [[Paragraph(f"<b>{h}</b>", s["centre"]) for h in headings]]

    items = list(invoice.items) if invoice.items else []
    for number, item in enumerate(items, 1):
        product = item.product
        rows.append([
            Paragraph(str(number), s["centre"]),
            Paragraph(text_or_dash(item.dc_number), s["centre"]),
            Paragraph(item.dc_date.strftime("%d/%m/%y") if item.dc_date else "-", s["centre"]),
            Paragraph(product.product_name, s["tiny"]),
            Paragraph(text_or_dash(item.dia), s["centre"]),
            Paragraph(f"{item.rolls:g}" if item.rolls is not None else "-", s["right"]),
            Paragraph(qty(item.quantity, 3), s["right"]),
            Paragraph(format_amount(item.rate), s["right"]),
            Paragraph(format_amount(item.amount), s["right"]),
        ])
    if not items:
        rows.append([Paragraph("No items added to this invoice.", s["centre"])])

    rows.append(
        [Paragraph("", s["tiny"])] * 6
        + [Paragraph("<b>TOTAL :</b>", s["right"]), Paragraph("", s["right"]),
           Paragraph(f"<b>{money(invoice.subtotal)}</b>", s["right"])]
    )

    item_table = Table(rows, colWidths=[23, 42, 52, 130, 43, 38, 56, 50, 103], repeatRows=1)
    zebra = [("BACKGROUND", (0, r), (-1, r), ZEBRA_ROW) for r in range(1, len(rows) - 1) if r % 2 == 0]
    item_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), job_fill), ("TEXTCOLOR", (0, 0), (-1, 0), job_text),
        ("GRID", (0, 0), (-1, -1), 0.35, job_line), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (0, -1), (-1, -1), job_soft_fill),
        *zebra,
    ]))
    if not items:
        item_table.setStyle(TableStyle([("SPAN", (0, 1), (-1, 1))]))

    # --- Tax + grand total --------------------------------------------------
    tax_rows = [
        [Paragraph(label, s["bold_small"]), Paragraph(money(amount), s["right"])]
        for label, amount in tax_breakup_rows(invoice)
    ]
    tax_rows.append([
        Paragraph("Round Off", s["bold_small"]),
        Paragraph(money(getattr(invoice, "round_off", 0.0)), s["right"]),
    ])
    tax_rows.append([
        Paragraph("<b>GRAND TOTAL</b>", ParagraphStyle("GrandLabel", parent=s["bold_small"], fontSize=10, textColor=NAVY)),
        Paragraph(f"<b>{money(invoice.grand_total)}</b>", ParagraphStyle("GrandValue", parent=s["right"], fontSize=10)),
    ])
    taxes = Table(tax_rows, colWidths=[130, 100], hAlign="RIGHT")
    taxes.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, job_line),
        ("BACKGROUND", (0, -1), (-1, -1), job_fill),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    footer = Table([[
        Paragraph(f"<b>Rupees:</b> {text_or_dash(invoice.amount_words)}", s["small"]),
        Paragraph(f"For <b>{company_name}</b><br/><br/><br/>",
                  ParagraphStyle("Signature", parent=s["small"], alignment=1)),
    ]], colWidths=[350, 187])
    footer.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.7, job_line), ("LINEBEFORE", (1, 0), (1, -1), 0.5, job_line),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("BACKGROUND", (0, 0), (-1, -1), job_soft_fill),
    ]))

    story = [
        header, Spacer(1, 4), details, Spacer(1, 4), item_table, Spacer(1, 4),
        taxes, Spacer(1, 4),
        KeepTogether([footer, Spacer(1, 3), Paragraph("", s["tiny"])]),
    ]
    doc.build(story, canvasmaker=_NumberedCanvas)
    buffer.seek(0)
    return buffer


# ==========================================================================
# Standard tax invoice
# ==========================================================================
def generate_invoice_pdf(invoice: models.Invoice, company: models.CompanyDetails) -> io.BytesIO:
    if invoice.invoice_type == "job_work":
        return generate_job_work_invoice_pdf(invoice, company)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=40,
        title=f"Tax Invoice {getattr(invoice, 'invoice_number', '')}".strip(),
    )
    story: list = []
    s = _build_shared_styles()

    is_job_work = invoice.invoice_type == "job_work"
    document_title = "JOB WORK INVOICE" if is_job_work else "TAX INVOICE"

    # --- 1. Header: company block + invoice title/number -------------------
    company_name = company.company_name if company else "Your Textile Company"
    company_address = company.address if company else "123, Textile Market, Ring Road, Surat"
    company_gst = company.gst if company else "-"
    company_pan = company.pan if company else "-"

    company_info = [
        Paragraph(company_name, s["title"]),
        Spacer(1, 4),
        Paragraph(f"<b>Address:</b> {text_or_dash(company_address)}", s["body"]),
        Paragraph(f"<b>GSTIN:</b> {text_or_dash(company_gst)} | <b>PAN:</b> {text_or_dash(company_pan)}", s["body"]),
    ]

    logo = get_company_logo(company.logo if company else None)
    header_left = (
        Table([[logo, company_info]], colWidths=[80, 240], style=[
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ])
        if logo else company_info
    )

    header_right = [
        Paragraph(document_title, ParagraphStyle(
            "DocTitle", parent=s["title"], alignment=2,
            fontSize=18 if is_job_work else 22, textColor=ACCENT_BLUE,
        )),
        Spacer(1, 6),
        Paragraph(f"<b>Invoice No:</b> {text_or_dash(invoice.invoice_number)}",
                  ParagraphStyle("RightBold", parent=s["body_bold"], alignment=2)),
        Paragraph(f"<b>Date:</b> {invoice.invoice_date.strftime('%d-%b-%Y') if invoice.invoice_date else '-'}",
                  ParagraphStyle("RightText", parent=s["body"], alignment=2)),
    ]

    header_table = Table([[header_left, header_right]], colWidths=[320, 220])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6))
    story.append(_hr())
    story.append(Spacer(1, 12))

    # --- 2. Customer + shipping / job details -------------------------------
    cust = invoice.customer
    customer_info = [
        Paragraph("<b>Billed To:</b>", s["subtitle"]),
        Spacer(1, 4),
        Paragraph(f"<b>{cust.company_name}</b>", s["body_bold"]),
        Paragraph(f"Contact: {text_or_dash(cust.contact_person)}", s["body"]),
        Paragraph(f"Address: {text_or_dash(cust.address)}", s["body"]),
        Paragraph(f"GSTIN: {text_or_dash(cust.gst_number)} | PAN: {text_or_dash(cust.pan_number)}", s["body"]),
        Paragraph(f"Mobile: {text_or_dash(cust.mobile)}", s["body"]),
    ]

    if is_job_work:
        meta_heading = "Job Work Details:"
        meta_line_1 = f"<b>Job Reference:</b> {text_or_dash(invoice.job_work_reference)}"
        meta_line_2 = f"<b>Challan No:</b> {text_or_dash(invoice.challan_number)}"
        meta_line_3 = f"<b>Work Description:</b> {text_or_dash(invoice.job_work_description)}"
    else:
        meta_heading = "Shipping / Dispatch Details:"
        meta_line_1 = f"<b>Shipping Address:</b> {text_or_dash(cust.shipping_address or cust.address)}"
        meta_line_2 = f"<b>Transport:</b> {text_or_dash(invoice.transport)}"
        meta_line_3 = f"<b>Sale Order:</b> {text_or_dash(invoice.sale_order)}"

    invoice_meta = [
        Paragraph(f"<b>{meta_heading}</b>", s["subtitle"]),
        Spacer(1, 4),
        Paragraph(meta_line_1, s["body"]),
        Spacer(1, 4),
        Paragraph(meta_line_2, s["body"]),
        Paragraph(meta_line_3, s["body"]),
        Paragraph(f"<b>Payment Terms:</b> {text_or_dash(invoice.payment_terms)}", s["body"]),
    ]

    details_table = Table([[customer_info, invoice_meta]], colWidths=[270, 270])
    details_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 15))

    # --- 3. Items table ------------------------------------------------------
    headings = ["S.No", "Product", "HSN", "Color", "Qty", "Unit", "Rate", "GST %", "Amount"]
    items_data = [[Paragraph(h, s["table_header"]) for h in headings]]

    items = list(invoice.items) if invoice.items else []
    for idx, item in enumerate(items, 1):
        prod = item.product
        items_data.append([
            Paragraph(str(idx), s["cell_centre"]),
            Paragraph(prod.product_name, s["cell"]),
            Paragraph(text_or_dash(prod.hsn), s["cell_centre"]),
            Paragraph(text_or_dash(prod.color), s["cell_centre"]),
            Paragraph(qty(item.quantity), s["cell_right"]),
            Paragraph(text_or_dash(prod.unit) if prod.unit else "Mtrs", s["cell_centre"]),
            Paragraph(money(item.rate), s["cell_right"]),
            Paragraph(f"{prod.gst_percentage:.1f}%", s["cell_centre"]),
            Paragraph(money(item.amount), s["cell_right"]),
        ])
    if not items:
        items_data.append([Paragraph("No items added to this invoice.", s["cell_centre"])])

    items_table = Table(items_data, colWidths=[30, 140, 50, 50, 45, 45, 55, 45, 80], repeatRows=1)
    zebra = [("BACKGROUND", (0, r), (-1, r), ZEBRA_ROW) for r in range(1, len(items_data)) if r % 2 == 0]
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GREY),
        *zebra,
    ]))
    if not items:
        items_table.setStyle(TableStyle([("SPAN", (0, 1), (-1, 1))]))
    story.append(items_table)
    story.append(Spacer(1, 10))

    # --- 4. Bank details + totals --------------------------------------------
    bank_name = company.bank_name if company else "-"
    ac_no = company.account_number if company else "-"
    ifsc = company.ifsc if company else "-"

    bank_details = [
        Paragraph("<b>Bank Transfer Information</b>", s["subtitle"]),
        Spacer(1, 4),
        Paragraph(f"<b>Bank Name:</b> {text_or_dash(bank_name)}", s["body"]),
        Paragraph(f"<b>A/c Number:</b> {text_or_dash(ac_no)}", s["body"]),
        Paragraph(f"<b>IFSC Code:</b> {text_or_dash(ifsc)}", s["body"]),
        Spacer(1, 8),
        Paragraph(f"<b>Remarks:</b> {text_or_dash(invoice.remarks) if invoice.remarks else 'Thank you for your business!'}", s["body"]),
    ]

    totals_rows = [[Paragraph("<b>Subtotal:</b>", s["body"]), Paragraph(money(invoice.subtotal), s["cell_right"])]]
    for label, amount in tax_breakup_rows(invoice):
        totals_rows.append([Paragraph(f"<b>{label}:</b>", s["body"]), Paragraph(money(amount), s["cell_right"])])
    totals_rows.append([
        Paragraph("<b>Round Off:</b>", s["body"]),
        Paragraph(money(getattr(invoice, "round_off", 0.0)), s["cell_right"]),
    ])
    totals_rows.append([
        Paragraph("<b>Grand Total:</b>", ParagraphStyle("GrandBold", parent=s["body_bold"], fontSize=11, textColor=NAVY)),
        Paragraph(f"<b>{money(invoice.grand_total)}</b>",
                  ParagraphStyle("GrandRight", parent=s["cell_right"], fontSize=11, fontName="Helvetica-Bold")),
    ])
    totals_table = Table(totals_rows, colWidths=[110, 110])
    totals_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ("BACKGROUND", (0, -1), (-1, -1), LIGHT_BLUE_BG),
    ]))

    financials_table = Table([[bank_details, totals_table]], colWidths=[320, 220])
    financials_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(financials_table)

    # --- 5. Amount in words + signature block (kept together) ---------------
    sig_left = [
        Paragraph("<b>Terms & Conditions:</b>", s["body_bold"]),
        Paragraph("1. Goods once sold will not be taken back.", s["body"]),
        Paragraph("2. Subject to Surat jurisdiction.", s["body"]),
    ]
    sig_right = [
        Paragraph(f"For <b>{company_name}</b>", ParagraphStyle("CenterBold", parent=s["body_bold"], alignment=1)),
        Spacer(1, 40),
        Paragraph("Authorized Signatory", ParagraphStyle("CenterText", parent=s["body"], alignment=1)),
    ]
    sig_table = Table([[sig_left, sig_right]], colWidths=[300, 240])
    sig_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    signature_section = [
        Spacer(1, 10),
        Paragraph(f"<b>Amount in Words:</b> <i>{text_or_dash(invoice.amount_words)}</i>", s["body"]),
        Spacer(1, 20),
        sig_table,
    ]
    story.append(KeepTogether(signature_section))

    doc.build(story, canvasmaker=_NumberedCanvas)
    buffer.seek(0)
    return buffer


def _hr(width: float = 540, color=BORDER_GREY, thickness: float = 0.75):
    """A thin horizontal rule used to separate the header from the body."""
    line = Table([[""]], colWidths=[width], rowHeights=[thickness])
    line.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), color)]))
    return line
