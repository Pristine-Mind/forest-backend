from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _build_table(headers, rows):
    data = [headers] + rows
    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4B5563")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    return table


def generate_pdf(title, headers, rows):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elements = [Paragraph(title, styles["Heading1"]), Spacer(1, 12)]
    elements.append(_build_table(headers, rows))
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_tree_count_pdf(tree_counts):
    headers = ["Species", "Block", "Total", "Harvested", "Remaining"]
    rows = [
        [
            item["species"],
            item["block"] or "All blocks",
            str(item["total_count"]),
            str(item["harvested_count"]),
            str(item["remaining_count"]),
        ]
        for item in tree_counts
    ]
    return generate_pdf("Tree Count Report", headers, rows)


def generate_harvest_pdf(harvest_summary):
    headers = ["Source Type", "Status", "Count", "Total Quantity"]
    rows = [
        [item["source_type"], item["status"], str(item["count"]), str(item["total_quantity"] or 0)]
        for item in harvest_summary
    ]
    return generate_pdf("Harvest Report", headers, rows)


def generate_stock_register_pdf(stock_register):
    headers = ["Species", "Grade", "Quantity Available"]
    rows = [[item["species"], item["grade"], str(item["quantity_available"])] for item in stock_register]
    return generate_pdf("Stock Register", headers, rows)


def generate_sales_pdf(sales_summary):
    headers = ["Buyer Type", "Count", "Total Quantity", "Total Amount"]
    rows = [
        [
            item["buyer_type"],
            str(item["count"]),
            str(item["total_quantity"] or 0),
            str(item["total_amount"] or 0),
        ]
        for item in sales_summary
    ]
    return generate_pdf("Sales Report", headers, rows)


def generate_visitor_entries_pdf(visitor_entries):
    headers = ["Visit Purpose", "Count", "Total Amount"]
    rows = [[item["visit_purpose"], str(item["count"]), str(item["total_amount"] or 0)] for item in visitor_entries]
    return generate_pdf("Visitor Entry Report", headers, rows)


def generate_fund_audit_pdf(fund_audit):
    headers = ["Metric", "Value"]
    rows = [
        ["Total Income", str(fund_audit["total_income"])],
        ["Total Expense", str(fund_audit["total_expense"])],
        ["Net", str(fund_audit["net"])],
    ]
    return generate_pdf("Fund & Audit Report", headers, rows)


def generate_governance_pdf(governance):
    headers = ["Metric", "Value"]
    rows = [
        ["Committee Total", str(governance["committee_total"])],
        ["Female Members", str(governance["female_members"])],
        ["Elections Held", str(governance["elections_held"])],
    ]
    return generate_pdf("Governance Report", headers, rows)


def generate_livelihood_pdf(livelihood):
    headers = ["Type", "Status / Program Type", "Count", "Total"]
    rows = []
    for loan in livelihood["loans"]:
        rows.append(["Loan", loan["status"], str(loan["count"]), str(loan["total"] or 0)])
    for program in livelihood["programs"]:
        rows.append(["Program", program["program_type"], str(program["count"]), str(program["total"] or 0)])
    return generate_pdf("Livelihood Programs Report", headers, rows)


def generate_offense_pdf(offense):
    headers = ["Metric", "Value"]
    rows = [
        ["Total Fines", str(offense["total_fines"])],
        ["Total Rewards", str(offense["total_rewards"])],
    ]
    for item in offense["by_status"]:
        rows.append([f"Status: {item['status']}", str(item["count"])])
    return generate_pdf("Offense Report", headers, rows)


def generate_annual_dfo_pdf(annual_dfo):
    headers = ["Metric", "Value"]
    rows = [[key.replace("_", " ").title(), str(value)] for key, value in annual_dfo.items()]
    return generate_pdf("Annual DFO Report", headers, rows)
