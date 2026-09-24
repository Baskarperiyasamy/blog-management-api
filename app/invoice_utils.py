import os
import uuid
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

MEDIA_ROOT = "media"
INVOICES_SUBDIR = "invoices"


def ensure_invoice_dir() -> None:
    os.makedirs(os.path.join(MEDIA_ROOT, INVOICES_SUBDIR), exist_ok=True)


def generate_transaction_id() -> str:
    return f"TXN-{uuid.uuid4().hex[:10].upper()}"


def generate_invoice_pdf(
    *,
    user_name: str,
    plan_name: str,
    price: float,
    start_date: datetime,
    end_date: datetime,
    transaction_id: str,
) -> str:
    """
    Renders a simple one-page invoice PDF and saves it under
    media/invoices/<uuid>.pdf. Returns the relative path (for storing in
    BillingHistory.invoice_path).
    """
    ensure_invoice_dir()

    filename = f"{uuid.uuid4().hex}.pdf"
    relative_path = os.path.join(INVOICES_SUBDIR, filename).replace("\\", "/")
    full_path = os.path.join(MEDIA_ROOT, relative_path)

    c = canvas.Canvas(full_path, pagesize=A4)
    width, height = A4

    # Header
    c.setFillColor(colors.HexColor("#2F5496"))
    c.rect(0, height - 30 * mm, width, 30 * mm, fill=True, stroke=False)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(20 * mm, height - 19 * mm, "Blog Management API")
    c.setFont("Helvetica", 11)
    c.drawString(20 * mm, height - 26 * mm, "Subscription Invoice")

    # Invoice meta
    c.setFillColor(colors.black)
    y = height - 45 * mm
    c.setFont("Helvetica", 11)
    rows = [
        ("Transaction ID", transaction_id),
        ("Invoice Date", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")),
        ("User Name", user_name),
        ("Plan", plan_name.capitalize()),
        ("Price", f"${price:.2f}"),
        ("Billing Period Start", start_date.strftime("%Y-%m-%d")),
        ("Billing Period End", end_date.strftime("%Y-%m-%d")),
    ]
    label_x = 20 * mm
    value_x = 80 * mm
    for label, value in rows:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(label_x, y, f"{label}:")
        c.setFont("Helvetica", 11)
        c.drawString(value_x, y, str(value))
        y -= 9 * mm

    # Divider + total
    y -= 4 * mm
    c.setStrokeColor(colors.HexColor("#CCCCCC"))
    c.line(20 * mm, y, width - 20 * mm, y)
    y -= 10 * mm
    c.setFont("Helvetica-Bold", 13)
    c.drawString(label_x, y, f"Amount Paid: ${price:.2f}")

    # Footer note
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(colors.HexColor("#888888"))
    c.drawString(
        20 * mm, 15 * mm,
        "This is a system-generated invoice for demo/testing purposes.",
    )

    c.showPage()
    c.save()

    return relative_path
