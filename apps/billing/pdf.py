from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_receipt_pdf(receipt):
    """Generate a PDF receipt and return it as a BytesIO buffer."""

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    elements = [
        Paragraph("Community Forest User Group", styles["Heading1"]),
        Paragraph("Official Receipt", styles["Heading2"]),
        Spacer(1, 20),
    ]

    data = [
        ["Receipt No", receipt.receipt_no],
        ["Date", str(receipt.issued_date)],
        ["Type", receipt.get_reference_type_display()],
        ["Amount", f"NPR {receipt.amount}"],
        ["Issued By", receipt.issued_by.full_name if receipt.issued_by else "N/A"],
    ]

    table = Table(data, colWidths=[150, 300])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E5E7EB")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer
