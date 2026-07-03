import os
from datetime import datetime
from io import BytesIO

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_receipt_pdf(receipt):
    """
    Generate beautiful official receipt PDF.
    """

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=35,
        leftMargin=35,
        topMargin=30,
        bottomMargin=30,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#166534"),
        fontSize=22,
        spaceAfter=4,
    )

    sub_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=11,
        textColor=colors.grey,
    )

    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        textColor=colors.white,
        alignment=TA_CENTER,
        backColor=colors.HexColor("#166534"),
        spaceAfter=12,
        spaceBefore=10,
        fontSize=14,
    )

    normal = styles["Normal"]

    elements = []

    ###################################################
    # Logo
    ###################################################

    logo_path = os.path.join(settings.BASE_DIR, "static", "logo.jpeg")

    if os.path.exists(logo_path):
        logo = Image(logo_path, width=0.9 * inch, height=0.9 * inch)
        logo.hAlign = "CENTER"
        elements.append(logo)

    ###################################################
    # Header
    ###################################################

    elements.append(Paragraph("<b>ShivGanga Community Forest</b>", title_style))

    elements.append(
        Paragraph(
            "ShivGanga Municipality-03, Kailali",
            sub_style,
        )
    )

    elements.append(
        Paragraph(
            "<font size=9>Email: info@shivganga.org | Phone: 9858426592</font>",
            sub_style,
        )
    )

    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", color=colors.darkgreen))
    elements.append(Spacer(1, 15))

    ###################################################
    # Receipt Heading
    ###################################################

    elements.append(Paragraph("OFFICIAL RECEIPT", heading_style))

    ###################################################
    # Receipt Information
    ###################################################

    data = [
        ["Receipt No.", receipt.receipt_no],
        ["Issued Date", receipt.issued_date.strftime("%d %B %Y")],
        ["Reference Type", receipt.get_reference_type_display()],
        ["Amount", f"NPR {receipt.amount:,.2f}"],
        [
            "Issued By",
            receipt.issued_by.full_name if receipt.issued_by else "N/A",
        ],
    ]

    table = Table(data, colWidths=[160, 310])

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E8F5E9")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    elements.append(table)

    ###################################################
    # Amount Box
    ###################################################

    elements.append(Spacer(1, 25))

    amount_table = Table(
        [
            [
                Paragraph(
                    f"<b>Total Amount Received : NPR {receipt.amount:,.2f}</b>",
                    ParagraphStyle(
                        "amount",
                        parent=styles["Heading2"],
                        alignment=TA_CENTER,
                        textColor=colors.white,
                    ),
                )
            ]
        ],
        colWidths=[470],
    )

    amount_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#15803D")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#166534")),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )

    elements.append(amount_table)

    ###################################################
    # Notes
    ###################################################

    elements.append(Spacer(1, 30))

    elements.append(
        Paragraph(
            "<b>Remarks</b><br/>"
            "This receipt is computer generated and serves as an official "
            "proof of payment for the above transaction.",
            normal,
        )
    )

    ###################################################
    # Signature
    ###################################################

    elements.append(Spacer(1, 60))

    signature = Table(
        [
            [
                "",
                "______________________________",
            ],
            [
                "",
                "Authorized Signature",
            ],
        ],
        colWidths=[250, 220],
    )

    signature.setStyle(
        TableStyle(
            [
                ("ALIGN", (1, 0), (1, -1), "CENTER"),
                ("FONTNAME", (1, 1), (1, 1), "Helvetica-Bold"),
            ]
        )
    )

    elements.append(signature)

    ###################################################
    # Footer
    ###################################################

    elements.append(Spacer(1, 30))
    elements.append(HRFlowable(width="100%", color=colors.grey))
    elements.append(Spacer(1, 5))

    elements.append(
        Paragraph(
            f"<font size=8 color='grey'>"
            f"Generated on {datetime.now().strftime('%d %B %Y %I:%M %p')} | "
            f"ShivGanga Community Forest Management System"
            f"</font>",
            ParagraphStyle(
                "footer",
                parent=styles["Normal"],
                alignment=TA_CENTER,
            ),
        )
    )

    doc.build(elements)

    buffer.seek(0)

    return buffer
