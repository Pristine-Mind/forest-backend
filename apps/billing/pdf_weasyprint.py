import os
from datetime import datetime
from io import BytesIO

from django.conf import settings


# Path to bundled Devanagari-capable font files.
# Download Noto Sans Devanagari (Regular + Bold) from Google Fonts and place
# them here, e.g.: <app>/static/fonts/NotoSansDevanagari-Regular.ttf
FONT_DIR = os.path.join(settings.BASE_DIR, "static", "fonts")
FONT_REGULAR = os.path.join(FONT_DIR, "NotoSansDevanagari-Regular.ttf")
FONT_BOLD = os.path.join(FONT_DIR, "NotoSansDevanagari-Bold.ttf")


def generate_receipt_pdf_weasyprint(receipt):
    try:
        from weasyprint import HTML, CSS
    except ImportError:
        print("! WeasyPrint not installed. Falling back to ReportLab.")
        from apps.billing.pdf import generate_receipt_pdf

        return generate_receipt_pdf(receipt)

    # Get receipt data
    receipt_no = getattr(receipt, "receipt_no", "")
    registration_no = getattr(receipt, "registration_no", "२६४")
    issued_date = getattr(receipt, "issued_date", None)
    issued_date_str = issued_date.strftime("%d/%m/%Y") if issued_date else ""
    customer_name = getattr(receipt, "customer_name", "") or ""
    amount = getattr(receipt, "amount", 0) or 0
    amount_in_words = getattr(receipt, "amount_in_words", "") or ""
    issued_by = getattr(receipt, "issued_by", None)
    issued_by_name = getattr(issued_by, "full_name", "") if issued_by else ""

    # Get reference details
    reference_type = getattr(receipt, "reference_type", "")
    reference_id = getattr(receipt, "reference_id", 0)

    description_text = ""
    quantity = ""
    rate = ""
    remarks = ""

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
                f"{visitor.fee_per_person:,.2f}" if hasattr(visitor, "fee_per_person") and visitor.fee_per_person > 0 else ""
            )
            remarks = visitor.purpose or ""
        except Exception:
            pass

    if not description_text:
        description = getattr(receipt, "get_reference_type_display", None)
        description_text = description() if callable(description) else reference_type

    # Font-face block: embeds the actual font files into the PDF so Nepali
    # (Devanagari) glyphs render regardless of what's installed on the host.
    # file:// URIs must be absolute paths.
    font_face_css = ""
    if os.path.exists(FONT_REGULAR):
        font_face_css += f"""
            @font-face {{
                font-family: 'NotoDevanagari';
                src: url('file://{FONT_REGULAR}');
                font-weight: normal;
            }}
        """
    if os.path.exists(FONT_BOLD):
        font_face_css += f"""
            @font-face {{
                font-family: 'NotoDevanagari';
                src: url('file://{FONT_BOLD}');
                font-weight: bold;
            }}
        """
    if not font_face_css:
        print(
            f"! Devanagari font files not found in {FONT_DIR}. "
            "Nepali text may not render correctly. "
            "Download NotoSansDevanagari-Regular.ttf / -Bold.ttf from Google Fonts."
        )

    # Generate HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            {font_face_css}

            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: 'NotoDevanagari', 'Noto Sans Devanagari', 'Noto Sans', Arial, sans-serif;
                font-size: 11pt;
                line-height: 1.4;
                padding: 20px;
                background-color: white;
                color: black;
            }}

            .receipt {{
                max-width: 210mm;
                margin: 0 auto;
                background: white;
                border: 1px solid #ccc;
                padding: 20px;
            }}

            .header {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 20px;
                border-bottom: 1px solid #000;
                padding-bottom: 10px;
            }}

            .receipt-no {{
                border: 2px solid black;
                padding: 8px 12px;
                font-size: 14pt;
                font-weight: bold;
                text-align: center;
                min-width: 50px;
            }}

            .org-info {{
                text-align: center;
                flex: 1;
            }}

            .org-name {{
                font-size: 14pt;
                font-weight: bold;
                margin-bottom: 3px;
            }}

            .org-address {{
                font-size: 10pt;
                color: #333;
            }}

            .registration {{
                text-align: right;
                font-size: 10pt;
            }}

            .registration-item {{
                margin-bottom: 3px;
            }}

            .title {{
                text-align: center;
                font-size: 13pt;
                font-weight: bold;
                margin: 15px 0;
            }}

            .field-line {{
                display: flex;
                margin-bottom: 12px;
                border-bottom: 1px solid #000;
                padding-bottom: 3px;
            }}

            .field-label {{
                flex: 0 0 70px;
                text-align: right;
                margin-right: 10px;
            }}

            .field-value {{
                flex: 1;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
            }}

            th, td {{
                border: 1px solid #000;
                padding: 6px 8px;
                text-align: left;
            }}

            th {{
                background-color: #f5f5f5;
                font-weight: bold;
                text-align: center;
                font-size: 9pt;
                padding: 8px 4px;
                line-height: 1.3;
            }}

            td {{
                font-size: 10pt;
                height: 24px;
            }}

            .col-qty {{
                text-align: center;
                width: 60px;
            }}

            .col-rate {{
                text-align: center;
                width: 60px;
            }}

            .col-amount {{
                text-align: center;
                width: 80px;
            }}

            .total-row {{
                font-weight: bold;
                background-color: #f9f9f9;
                height: 26px;
            }}

            .total-row td:nth-child(3) {{
                text-align: right;
            }}

            .amount-words {{
                display: flex;
                margin: 10px 0;
                border-bottom: 1px solid #000;
                padding-bottom: 3px;
            }}

            .amount-words-label {{
                flex: 0 0 100px;
                text-align: right;
                margin-right: 10px;
            }}

            .amount-words-value {{
                flex: 1;
            }}

            .signature-section {{
                display: flex;
                justify-content: space-between;
                margin-top: 30px;
            }}

            .signature {{
                text-align: center;
                flex: 1;
            }}

            .signature-line {{
                border-top: 1px solid #000;
                width: 150px;
                margin: 30px auto 5px;
            }}

            .signature-text {{
                font-size: 9pt;
                margin-top: 3px;
            }}

            .footer {{
                text-align: center;
                font-size: 8pt;
                color: #666;
                margin-top: 20px;
                border-top: 1px solid #ddd;
                padding-top: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="receipt">
            <div class="header">
                <div class="receipt-no">{receipt_no}</div>
                <div class="org-info">
                    <div class="org-name">श्री शिवगंगा सामुदायिक वन उपभोक्ता समूह</div>
                    <div class="org-address">Shivganga Community Forest User Group</div>
                    <div class="org-address">गौरीगंगा न.पा.-३, कुचैनी, कैलाली</div>
                    <div class="org-address">Gauriganga Municipality-3, Kuchain, Kailali</div>
                </div>
                <div class="registration">
                    <div class="registration-item"><strong>Registration No. (दर्ता नं.):</strong> {registration_no}</div>
                    <div class="registration-item"><strong>Date (मिति):</strong> {issued_date_str}</div>
                </div>
            </div>

            <div class="title">नगदी रसिद (Receipt)</div>

            <div class="field-line">
                <div class="field-label">Name (नाम):</div>
                <div class="field-value">{customer_name}</div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>विवरण<br/>(Description)</th>
                        <th class="col-qty">परिमाण<br/>(Qty)</th>
                        <th class="col-rate">दर<br/>(Rate)</th>
                        <th class="col-amount">रकम<br/>(Amount)</th>
                        <th>कैफियत<br/>(Remarks)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{description_text}</td>
                        <td class="col-qty">{quantity}</td>
                        <td class="col-rate">{rate}</td>
                        <td class="col-amount">{amount:,.2f}</td>
                        <td>{remarks}</td>
                    </tr>
                    <tr><td colspan="5"></td></tr>
                    <tr><td colspan="5"></td></tr>
                    <tr class="total-row">
                        <td colspan="2"></td>
                        <td style="text-align: right;">जम्मा रकम (Total)</td>
                        <td class="col-amount">{amount:,.2f}</td>
                        <td></td>
                    </tr>
                </tbody>
            </table>

            <div class="amount-words">
                <div class="amount-words-label">अक्षरुपी रू (Amount in Words):</div>
                <div class="amount-words-value">{amount_in_words}</div>
            </div>

            <div style="margin-top: 30px; display: flex; justify-content: space-between;">
                <div class="signature">
                    <div class="signature-line"></div>
                    <div class="signature-text">बुझाइनेको सही<br/>(Received by)</div>
                </div>
                <div class="signature">
                    <div class="signature-line"></div>
                    <div class="signature-text">बुझिलिनेको सही<br/>(Issued by: {issued_by_name})</div>
                </div>
            </div>

            <div class="footer">
                Generated on {datetime.now().strftime("%d %B %Y %H:%M:%S")} | ShivGanga Community Forest Management System
                This is a system-generated receipt.
            </div>
        </div>
    </body>
    </html>
    """

    try:
        # Generate PDF from HTML
        pdf_file = HTML(string=html_content).write_pdf()
        buffer = BytesIO(pdf_file)
        return buffer
    except Exception as e:
        print(f"Error generating PDF with WeasyPrint: {e}")
        # Fall back to ReportLab
        from apps.billing.pdf import generate_receipt_pdf

        return generate_receipt_pdf(receipt)
