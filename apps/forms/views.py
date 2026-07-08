import io

from django.http import FileResponse
from django.template.loader import render_to_string
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.permissions import IsAuthenticatedReadOnly

from .models import (
    CuttingRegister,
    CuttingRegisterItem,
    FellingRegister,
    FellingRegisterEntry,
    ForestProductReceipt,
    TreeSurveyForm,
    TreeSurveyFormItem,
)
from .serializers import (
    CuttingRegisterItemSerializer,
    CuttingRegisterSerializer,
    FellingRegisterEntrySerializer,
    FellingRegisterSerializer,
    ForestProductReceiptSerializer,
    TreeSurveyFormItemSerializer,
    TreeSurveyFormSerializer,
)


class TreeSurveyFormViewSet(viewsets.ModelViewSet):
    """ViewSet for tree survey forms with PDF export"""

    queryset = TreeSurveyForm.objects.all().prefetch_related("tree_items__species")
    serializer_class = TreeSurveyFormSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["block", "operational_plan", "survey_date"]
    search_fields = ["form_number", "district", "municipality"]
    ordering_fields = ["-survey_date", "form_number"]
    ordering = ["-survey_date"]

    @action(detail=True, methods=["get"], url_path="pdf")
    def export_pdf(self, request, pk=None):
        """Export survey form as PDF"""
        form = self.get_object()

        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=14,
            textColor=colors.HexColor("#333333"),
            spaceAfter=6,
            alignment=1,  # Center alignment
        )
        story.append(Paragraph("अनुसूची-७ प्लटबाट प्राप्तकोसिम काठ, बाउरा खुवाई गरेर विक्रेचलानी पूर्जी", title_style))
        story.append(Paragraph("Schedule 7 - Tree Survey and Collection Form", title_style))
        story.append(Spacer(1, 0.2 * inch))

        # Form header info
        header_data = [
            ["रामा पूर्जी न्:", form.form_number, "कटबा गरेर निकासको नाम :", form.district],
            ["क्षेत्र :", form.block.block_name, "रुख मसिला :", form.species],
            ["यस-बिजिमान :", form.municipality, "कटबा खेत्र छ याम :", ""],
            ["खण्ड/खेतको नाम र निमिनि :", f"{form.ward_number}", "पाटाइको स्थान :", ""],
        ]

        header_table = Table(header_data, colWidths=[2 * inch, 2 * inch, 2 * inch, 2 * inch])
        header_table.setStyle(
            TableStyle(
                [
                    ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.beige),
                ]
            )
        )
        story.append(header_table)
        story.append(Spacer(1, 0.2 * inch))

        # Tree items table
        items_data = [
            [
                "किसिम",
                "इस्पात निकासको किसिम",
                "खान्चको नाम",
                "काठको आयत",
                "गोलाई न.",
                "लाइड",
                "आयतन",
                "चुरा",
                "छोटिकरन",
            ]
        ]

        for item in form.tree_items.all():
            items_data.append(
                [
                    str(item.serial_number),
                    item.get_wood_type_display(),
                    item.species.species_name,
                    "",
                    str(item.girth_cm),
                    str(item.height_m),
                    f"{item.volume_cubic_m:.3f}",
                    "",
                    f"{item.fuelwood_volume_cubic_m:.3f}",
                ]
            )

        # Add totals row
        total_volume = form.get_total_volume()
        total_fuelwood = form.get_total_fuelwood()
        items_data.append(
            [
                "",
                "",
                "जम्मा (Total)",
                "",
                "",
                "",
                f"{total_volume:.3f}",
                "",
                f"{total_fuelwood:.3f}",
            ]
        )

        items_table = Table(items_data, colWidths=[0.5 * inch] * 9)
        items_table.setStyle(
            TableStyle(
                [
                    ("FONT", (0, 0), (-1, -1), "Helvetica", 8),
                    ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
                    ("FONT", (0, -1), (-1, -1), "Helvetica-Bold", 9),
                ]
            )
        )
        story.append(items_table)
        story.append(Spacer(1, 0.3 * inch))

        # Signatures
        sig_data = [
            ["समुदायिक बन उपभोक्ता प्रतिनिधि", "", "वन प्रतिनिधि"],
            ["नाम :", form.community_representative or "_" * 20, "नाम :", form.forest_officer or "_" * 20],
            ["पद :", "_" * 20, "पद :", "_" * 20],
            ["दस्तखत :", "_" * 20, "दस्तखत :", "_" * 20],
            ["मिति :", "_" * 20, "मिति :", "_" * 20],
        ]

        sig_table = Table(sig_data, colWidths=[2.5 * inch, 0.5 * inch, 2.5 * inch])
        sig_table.setStyle(
            TableStyle(
                [
                    ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        story.append(sig_table)

        # Build PDF
        doc.build(story)
        buffer.seek(0)

        # Return PDF file
        response = FileResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="survey_form_{form.form_number}.pdf"'
        return response

    @action(detail=False, methods=["post"], url_path="bulk-pdf")
    def export_bulk_pdf(self, request):
        """Export multiple survey forms as a single PDF"""
        form_ids = request.data.get("form_ids", [])
        forms = TreeSurveyForm.objects.filter(id__in=form_ids).prefetch_related("tree_items__species")

        if not forms.exists():
            return Response({"error": "No forms found"}, status=status.HTTP_404_NOT_FOUND)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        for idx, form in enumerate(forms):
            if idx > 0:
                story.append(PageBreak())

            # Same content as single PDF export
            title_style = ParagraphStyle(
                "CustomTitle",
                parent=styles["Heading1"],
                fontSize=12,
                textColor=colors.HexColor("#333333"),
                spaceAfter=6,
            )
            story.append(Paragraph(f"Form {form.form_number} - {form.block.block_name}", title_style))

            # Items table
            items_data = [["किसिम", "खान्चको नाम", "गोलाई न.", "आयतन", "चुरा"]]

            for item in form.tree_items.all():
                items_data.append(
                    [
                        str(item.serial_number),
                        item.species.species_name,
                        str(item.girth_cm),
                        f"{item.volume_cubic_m:.3f}",
                        f"{item.fuelwood_volume_cubic_m:.3f}",
                    ]
                )

            items_table = Table(items_data, colWidths=[1 * inch] * 5)
            items_table.setStyle(
                TableStyle(
                    [
                        ("FONT", (0, 0), (-1, -1), "Helvetica", 8),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )
            story.append(items_table)
            story.append(Spacer(1, 0.2 * inch))

        doc.build(story)
        buffer.seek(0)

        response = FileResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="survey_forms_{timezone.now().date()}.pdf"'
        return response


class TreeSurveyFormItemViewSet(viewsets.ModelViewSet):
    """ViewSet for tree items within survey forms"""

    queryset = TreeSurveyFormItem.objects.all().select_related("species", "survey_form")
    serializer_class = TreeSurveyFormItemSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["survey_form", "species"]
    search_fields = ["species__species_name"]
    ordering = ["survey_form", "serial_number"]


class CuttingRegisterViewSet(viewsets.ModelViewSet):
    """ViewSet for cutting registers with PDF export"""

    queryset = CuttingRegister.objects.all().prefetch_related("cutting_items__species")
    serializer_class = CuttingRegisterSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["block", "operational_plan", "register_date"]
    search_fields = ["form_number", "district", "municipality"]
    ordering_fields = ["-register_date", "form_number"]
    ordering = ["-register_date"]

    @action(detail=True, methods=["get"], url_path="pdf")
    def export_pdf(self, request, pk=None):
        """Export cutting register as PDF"""
        register = self.get_object()

        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=14,
            textColor=colors.HexColor("#333333"),
            spaceAfter=6,
            alignment=1,  # Center alignment
        )
        story.append(Paragraph("अनुसूची-८ घाटागीरो/कटान रजिस्टर", title_style))
        story.append(Paragraph("Schedule 8 - Cutting/Ghaat Register", title_style))
        story.append(Spacer(1, 0.2 * inch))

        # Register header info
        header_data = [
            ["क्षेत्र :", register.zone, "वन-क्षिजिञयात :", register.forest_classification],
            ["जिल्ला :", register.district, "खण्ड/प्लटको नाम :", register.block_plot_name],
            ["गाउँपालिका :", register.municipality, "खण्ड/प्लटको किसिम :", register.block_plot_type],
            ["वार्ड नं. :", str(register.ward_number), "घाटागीरोको स्थान :", register.cutting_location],
        ]

        header_table = Table(header_data, colWidths=[1.5 * inch, 2 * inch, 2 * inch, 2.5 * inch])
        header_table.setStyle(
            TableStyle(
                [
                    ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.beige),
                ]
            )
        )
        story.append(header_table)
        story.append(Spacer(1, 0.2 * inch))

        # Cutting items table
        items_data = [["मिमिट", "समय", "रमाना न.", "गोपिया न.", "जात", "नाप साइज", "आयतन", "दादुरा", "कैफियत"]]

        for item in register.cutting_items.all():
            items_data.append(
                [
                    str(item.serial_number),
                    item.entry_time.strftime("%H:%M") if item.entry_time else "",
                    item.plot_number,
                    item.quota_number or "",
                    item.species.species_name,
                    item.size_measurement,
                    str(item.volume_cubic_m),
                    item.comments or "",
                    item.remarks or "",
                ]
            )

        items_table = Table(
            items_data,
            colWidths=[0.6 * inch, 0.7 * inch, 0.8 * inch, 0.8 * inch, 1 * inch, 1 * inch, 0.9 * inch, 0.9 * inch, 1 * inch],
        )
        items_table.setStyle(
            TableStyle(
                [
                    ("FONT", (0, 0), (-1, -1), "Helvetica", 8),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
                    ("FONT", (0, -1), (-1, -1), "Helvetica-Bold", 9),
                ]
            )
        )
        story.append(items_table)
        story.append(Spacer(1, 0.3 * inch))

        # Signatures
        sig_data = [
            ["सामुदायिक वनको प्रतिनिधि", "", "वन प्रतिनिधि"],
            ["नाम :", register.community_representative_name or "_" * 20, "नाम :", register.forest_officer_name or "_" * 20],
            [
                "पद :",
                register.community_representative_position or "_" * 20,
                "पद :",
                register.forest_officer_position or "_" * 20,
            ],
            ["दस्तखत :", "_" * 20, "दस्तखत :", "_" * 20],
            ["मिति :", "_" * 20, "मिति :", "_" * 20],
        ]

        sig_table = Table(sig_data, colWidths=[2.5 * inch, 0.5 * inch, 2.5 * inch])
        sig_table.setStyle(
            TableStyle(
                [
                    ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        story.append(sig_table)

        # Build PDF
        doc.build(story)
        buffer.seek(0)

        # Return PDF file
        response = FileResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="cutting_register_{register.form_number}.pdf"'
        return response


class CuttingRegisterItemViewSet(viewsets.ModelViewSet):

    queryset = CuttingRegisterItem.objects.all().select_related("species", "cutting_register")
    serializer_class = CuttingRegisterItemSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["cutting_register", "species"]
    search_fields = ["species__species_name", "plot_number"]
    ordering = ["cutting_register", "serial_number"]


class FellingRegisterViewSet(viewsets.ModelViewSet):
    queryset = FellingRegister.objects.all().prefetch_related("entries", "entries__species")
    serializer_class = FellingRegisterSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class FellingRegisterEntryViewSet(viewsets.ModelViewSet):
    queryset = FellingRegisterEntry.objects.all().select_related("species", "register")
    serializer_class = FellingRegisterEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        register_id = self.request.query_params.get("register")
        if register_id:
            qs = qs.filter(register_id=register_id)
        return qs


class ForestProductReceiptViewSet(viewsets.ModelViewSet):
    queryset = ForestProductReceipt.objects.prefetch_related("items", "sales")
    serializer_class = ForestProductReceiptSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["issue_date", "buyer_name"]
    search_fields = ["receipt_no", "buyer_name"]
