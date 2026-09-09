import os
from datetime import datetime
from io import BytesIO

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


FONT_REGULAR = "NotoSansDevanagari"
FONT_BOLD = "NotoSansDevanagari-Bold"
_FALLBACK_REGULAR = "Helvetica"
_FALLBACK_BOLD = "Helvetica-Bold"


def _register_devanagari_fonts():
    """
    Registers the Devanagari fonts with reportlab if not already registered.
    Falls back to Helvetica (which will render boxes/blanks for Devanagari
    text, not the actual script) if the font files are missing, so the PDF
    generation never hard-crashes in production.

    Returns (regular_font_name, bold_font_name) to actually use.
    """
    # Always try to register - some environments may clear the registry
    registered = pdfmetrics.getRegisteredFontNames()

    # If already registered in this process, return early
    if FONT_REGULAR in registered and FONT_BOLD in registered:
        return FONT_REGULAR, FONT_BOLD

    # Try multiple possible paths for fonts
    possible_paths = [
        os.path.join(settings.BASE_DIR, "static", "fonts"),  # Development
        os.path.join(settings.BASE_DIR, "..", "static", "fonts"),  # Alternative
        "/code/static/fonts",  # Docker
        "/app/static/fonts",  # Docker alternative
    ]

    fonts_found = False
    fonts_dir = None

    for path in possible_paths:
        regular_path = os.path.join(path, "NotoSansDevanagari-Regular.ttf")
        bold_path = os.path.join(path, "NotoSansDevanagari-Bold.ttf")

        if os.path.exists(regular_path) and os.path.exists(bold_path):
            # Verify files have content
            if os.path.getsize(regular_path) > 0 and os.path.getsize(bold_path) > 0:
                fonts_dir = path
                fonts_found = True
                break

    if fonts_found and fonts_dir:
        try:
            regular_path = os.path.join(fonts_dir, "NotoSansDevanagari-Regular.ttf")
            bold_path = os.path.join(fonts_dir, "NotoSansDevanagari-Bold.ttf")

            print(f"Registering fonts from {fonts_dir}...")
            print(f"  Regular: {regular_path} ({os.path.getsize(regular_path)} bytes)")
            print(f"  Bold: {bold_path} ({os.path.getsize(bold_path)} bytes)")

            pdfmetrics.registerFont(TTFont(FONT_REGULAR, regular_path))
            pdfmetrics.registerFont(TTFont(FONT_BOLD, bold_path))

            # Verify they're actually registered
            registered = pdfmetrics.getRegisteredFontNames()
            if FONT_REGULAR in registered and FONT_BOLD in registered:
                print(f"✓ Successfully registered Devanagari fonts")
                return FONT_REGULAR, FONT_BOLD
            else:
                print(f"✗ Fonts not in registry after registration")
                print(f"  Available fonts: {len(registered)} registered")

        except Exception as e:
            print(f"✗ Error registering fonts: {e}")
            print(f"  Type: {type(e).__name__}")
            import traceback

            traceback.print_exc()
    else:
        if fonts_found:
            print(f"✗ Font files found but empty. Checked {fonts_dir}")
        else:
            print(f"✗ Devanagari fonts not found in any of:")
            for path in possible_paths:
                regular_path = os.path.join(path, "NotoSansDevanagari-Regular.ttf")
                bold_path = os.path.join(path, "NotoSansDevanagari-Bold.ttf")
                reg_exists = "✓" if os.path.exists(regular_path) else "✗"
                bold_exists = "✓" if os.path.exists(bold_path) else "✗"
                print(f"  {path}")
                print(f"    Regular: {reg_exists} ({regular_path})")
                print(f"    Bold: {bold_exists} ({bold_path})")

    # Font files not found — fall back so the app doesn't crash. Devanagari
    # text will not render correctly until the .ttf files are added.
    print(f"! Falling back to {_FALLBACK_REGULAR}. Nepali text may not render correctly.")
    return _FALLBACK_REGULAR, _FALLBACK_BOLD


def _ensure_utf8(text):
    """Ensure text is properly UTF-8 encoded for PDF rendering."""
    if isinstance(text, bytes):
        return text.decode("utf-8")
    return str(text) if text else ""


def generate_receipt_pdf(receipt):
    """
    Generates the official "जगदी रसिद" (goods/collection receipt) PDF,
    matching the printed carbon-copy receipt book design used by the
    forest user group.

    Expected `receipt` fields (with graceful fallbacks via getattr so this
    doesn't break if a field isn't on the model yet):
        receipt_no        (str/int)  - serial number printed in the box, e.g. "618"
        registration_no    (str)      - "दर्ता नं." value, e.g. "२६४"
        issued_date        (date)     - receipt date
        customer_name      (str)      - "...को नाम" — person/party the receipt is issued to
        amount             (Decimal)  - total amount (used for the जम्मा रकम row
                                          and as a fallback single line item)
        amount_in_words    (str)      - amount spelled out, for the "रू" line
        issued_by          (User)     - who issued/received it (used in
                                          the "बुझिलिनेको सही" line, optional)
        items              (related manager / iterable) - optional line items,
                                          each with: description, quantity,
                                          rate, amount, remarks

    If `receipt.items` doesn't exist, a single row is built from
    `receipt.amount` so the table still renders sensibly.
    """

    font_regular, font_bold = _register_devanagari_fonts()

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=28,
        leftMargin=28,
        topMargin=26,
        bottomMargin=26,
    )

    elements = []

    # ---------------------------------------------------------------
    # Shared styles
    # ---------------------------------------------------------------

    org_name_style = ParagraphStyle(
        "OrgName",
        fontName=font_bold,
        fontSize=17,
        alignment=TA_CENTER,
        textColor=colors.black,
        leading=20,
    )

    address_style = ParagraphStyle(
        "Address",
        fontName=font_regular,
        fontSize=10.5,
        alignment=TA_CENTER,
        textColor=colors.black,
        leading=13,
    )

    receipt_title_style = ParagraphStyle(
        "ReceiptTitle",
        fontName=font_bold,
        fontSize=14,
        alignment=TA_CENTER,
        textColor=colors.black,
    )

    box_style = ParagraphStyle(
        "Box",
        fontName=font_bold,
        fontSize=13,
        alignment=TA_CENTER,
        textColor=colors.black,
    )

    small_label_style = ParagraphStyle(
        "SmallLabel",
        fontName=font_regular,
        fontSize=10,
        alignment=TA_RIGHT,
        textColor=colors.black,
    )

    field_line_style = ParagraphStyle(
        "FieldLine",
        fontName=font_regular,
        fontSize=10.5,
        alignment=TA_LEFT,
        textColor=colors.black,
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        fontName=font_bold,
        fontSize=10.5,
        alignment=TA_CENTER,
        textColor=colors.black,
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        fontName=font_regular,
        fontSize=10,
        alignment=TA_LEFT,
        textColor=colors.black,
    )

    table_cell_center_style = ParagraphStyle(
        "TableCellCenter",
        fontName=font_regular,
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.black,
    )

    total_label_style = ParagraphStyle(
        "TotalLabel",
        fontName=font_bold,
        fontSize=11,
        alignment=TA_RIGHT,
        textColor=colors.black,
    )

    total_value_style = ParagraphStyle(
        "TotalValue",
        fontName=font_bold,
        fontSize=11,
        alignment=TA_CENTER,
        textColor=colors.black,
    )

    signature_style = ParagraphStyle(
        "Signature",
        fontName=font_regular,
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.black,
    )

    # ---------------------------------------------------------------
    # Field values (safe fallbacks so a leaner model doesn't crash this)
    # ---------------------------------------------------------------

    receipt_no = getattr(receipt, "receipt_no", "")
    registration_no = getattr(receipt, "registration_no", "")
    issued_date = getattr(receipt, "issued_date", None)
    issued_date_str = issued_date.strftime("%d/%m/%Y") if issued_date else ""
    customer_name = getattr(receipt, "customer_name", "") or ""
    amount = getattr(receipt, "amount", 0) or 0
    amount_in_words = getattr(receipt, "amount_in_words", "") or ""
    issued_by = getattr(receipt, "issued_by", None)
    issued_by_name = getattr(issued_by, "full_name", "") if issued_by else ""

    # ---------------------------------------------------------------
    # Logo (optional, kept from the original implementation)
    # ---------------------------------------------------------------

    logo_path = os.path.join(settings.BASE_DIR, "static", "logo.jpeg")
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=0.55 * inch, height=0.55 * inch)
        logo.hAlign = "CENTER"
        elements.append(logo)
        elements.append(Spacer(1, 4))

    # ---------------------------------------------------------------
    # Header block: receipt-no box | org name & address | दर्ता नं. + मिति
    # ---------------------------------------------------------------

    header_left = Table(
        [[Paragraph(str(receipt_no), box_style)]],
        colWidths=[42],
        rowHeights=[30],
    )
    header_left.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1.1, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )

    header_center = [
        Paragraph("श्री शिवगंगा सामुदायिक वन उपभोक्ता समूह", org_name_style),
        Paragraph("गौरीगंगा न.पा.-३, कुचैनी, कैलाली", address_style),
    ]

    header_right = Table(
        [
            [Paragraph(f"दर्ता नं. {registration_no}", small_label_style)],
            [Paragraph(f"मिति : {issued_date_str}", small_label_style)],
        ],
        colWidths=[100],
    )
    header_right.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    header_table = Table(
        [[header_left, header_center, header_right]],
        colWidths=[50, 360, 108],
    )
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
            ]
        )
    )

    elements.append(header_table)
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("जगदी रसिद", receipt_title_style))
    elements.append(Spacer(1, 10))

    # ---------------------------------------------------------------
    # Name line — dotted underline to mirror the pre-printed slip
    # ---------------------------------------------------------------

    name_line = Table(
        [
            [
                Paragraph("...... को नाम :", field_line_style),
                Paragraph(customer_name, field_line_style),
            ]
        ],
        colWidths=[70, 448],
    )
    name_line.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (1, 0), (1, 0), 0.6, colors.black),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    elements.append(name_line)
    elements.append(Spacer(1, 10))

    # ---------------------------------------------------------------
    # Item table: विवरण | परिमाण | दर | रकम | कैफियत
    # ---------------------------------------------------------------

    header_row = [
        Paragraph("विवरण", table_header_style),
        Paragraph("परिमाण", table_header_style),
        Paragraph("दर", table_header_style),
        Paragraph("रकम", table_header_style),
        Paragraph("कैफियत", table_header_style),
    ]

    items = getattr(receipt, "items", None)
    item_rows = []
    if items is not None:
        try:
            iterable_items = items.all()
        except AttributeError:
            iterable_items = items
        for item in iterable_items:
            item_rows.append(
                [
                    Paragraph(str(getattr(item, "description", "")), table_cell_style),
                    Paragraph(str(getattr(item, "quantity", "")), table_cell_center_style),
                    Paragraph(str(getattr(item, "rate", "")), table_cell_center_style),
                    Paragraph(f"{getattr(item, 'amount', 0):,.2f}", table_cell_center_style),
                    Paragraph(str(getattr(item, "remarks", "")), table_cell_style),
                ]
            )

    if not item_rows:
        # Fallback: Try to get details from related FeeCollection or VisitorEntry
        description_text = ""
        quantity = ""
        rate = ""
        remarks = ""

        reference_type = getattr(receipt, "reference_type", "")
        reference_id = getattr(receipt, "reference_id", 0)

        if reference_type == "fee_collection":
            try:
                from apps.billing.models import FeeCollection

                fee_collection = FeeCollection.objects.get(id=reference_id)
                fee_type_display = fee_collection.get_fee_type_display() or fee_collection.fee_type
                description_text = f"Fee Collection - {fee_type_display}"
                quantity = str(fee_collection.quantity) if fee_collection.quantity else ""
                rate = f"{fee_collection.rate:,.2f}" if fee_collection.rate > 0 else ""
                remarks = fee_collection.remarks or ""
            except Exception:
                pass
        elif reference_type == "visitor_entry":
            try:
                from apps.visitors.models import VisitorEntry

                visitor = VisitorEntry.objects.get(id=reference_id)
                description_text = f"Visitor Entry - {visitor.visitor_name}"
                quantity = str(visitor.number_of_visitors) if hasattr(visitor, "number_of_visitors") else ""
                rate = (
                    f"{visitor.fee_per_person:,.2f}"
                    if hasattr(visitor, "fee_per_person") and visitor.fee_per_person > 0
                    else ""
                )
                remarks = visitor.purpose or ""
            except Exception:
                pass

        if not description_text:
            # Last resort: use reference type display
            description = getattr(receipt, "get_reference_type_display", None)
            description_text = description() if callable(description) else reference_type

        item_rows.append(
            [
                Paragraph(str(description_text or ""), table_cell_style),
                Paragraph(str(quantity), table_cell_center_style),
                Paragraph(str(rate), table_cell_center_style),
                Paragraph(f"{amount:,.2f}", table_cell_center_style),
                Paragraph(str(remarks), table_cell_style),
            ]
        )

    # Pad with a couple of blank rows so short receipts still have the
    # open, spacious look of the printed pad.
    blank_rows_needed = max(0, 4 - len(item_rows))
    for _ in range(blank_rows_needed):
        item_rows.append([Paragraph("", table_cell_style)] * 5)

    total_row = [
        "",
        "",
        Paragraph("जम्मा रकम", table_header_style),
        Paragraph(f"{amount:,.2f}", total_value_style),
        "",
    ]

    table_data = [header_row] + item_rows + [total_row]

    col_widths = [178, 68, 68, 90, 90]

    item_table = Table(table_data, colWidths=col_widths, rowHeights=[26] + [24] * len(item_rows) + [26])

    span_start = 1 + len(item_rows)  # index of the total row
    item_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("SPAN", (0, span_start), (1, span_start)),
                ("ALIGN", (2, span_start), (2, span_start), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    elements.append(item_table)
    elements.append(Spacer(1, 10))

    # ---------------------------------------------------------------
    # Amount in words line
    # ---------------------------------------------------------------

    words_line = Table(
        [
            [
                Paragraph("अक्षरुपी रू :", field_line_style),
                Paragraph(amount_in_words, field_line_style),
            ]
        ],
        colWidths=[70, 448],
    )
    words_line.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (1, 0), (1, 0), 0.6, colors.black),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    elements.append(words_line)
    elements.append(Spacer(1, 40))

    # ---------------------------------------------------------------
    # Signatures — payer (left) and receiver (right), as on the slip
    # ---------------------------------------------------------------

    signature_table = Table(
        [
            [
                Paragraph("_________________________", signature_style),
                Paragraph("_________________________", signature_style),
            ],
            [
                Paragraph("बुझाउनेको सही", signature_style),
                Paragraph(
                    f"बुझिलिनेको सही{' (' + issued_by_name + ')' if issued_by_name else ''}",
                    signature_style,
                ),
            ],
        ],
        colWidths=[259, 259],
    )
    signature_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 1), (-1, 1), 2),
            ]
        )
    )
    elements.append(signature_table)

    # ---------------------------------------------------------------
    # Footer
    # ---------------------------------------------------------------

    elements.append(Spacer(1, 20))
    footer_style = ParagraphStyle(
        "Footer",
        fontName=font_regular,
        fontSize=7.5,
        alignment=TA_CENTER,
        textColor=colors.grey,
    )
    elements.append(
        Paragraph(
            f"Generated on {datetime.now().strftime('%d %B %Y %I:%M %p')} | "
            f"ShivGanga Community Forest Management System",
            footer_style,
        )
    )

    doc.build(elements)

    buffer.seek(0)

    return buffer
