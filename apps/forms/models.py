from django.core.validators import MinValueValidator
from django.db import models
from decimal import Decimal

from apps.core.models import AbstractBaseModel
from apps.forest.models import ForestBlock, OperationalPlan, Species
from apps.inventory.models import Sale


class TreeSurveyForm(AbstractBaseModel):
    """Survey form for tree collection/wood harvest (अनुसूची-७)"""

    # Form metadata
    form_number = models.CharField(max_length=50, unique=True, help_text="Form identification number (पूर्जी क्र.स.)")
    survey_date = models.DateField(help_text="Date of survey (मिति)")

    # Forest information
    block = models.ForeignKey(ForestBlock, on_delete=models.PROTECT, related_name="survey_forms", null=True, blank=True)
    operational_plan = models.ForeignKey(
        OperationalPlan, on_delete=models.PROTECT, null=True, blank=True, related_name="survey_forms"
    )

    # Spatial information
    district = models.CharField(max_length=255, help_text="जिल्ला")
    municipality = models.CharField(max_length=255, help_text="गाउँपालिका / नगरपालिका")
    ward_number = models.PositiveIntegerField(help_text="वार्ड नं.")

    # Plot information
    plot_number = models.PositiveIntegerField(help_text="प्लट नं.")
    forest_category = models.CharField(max_length=50, help_text="वन कक्षा")

    # Approvals
    community_representative = models.CharField(max_length=255, blank=True, help_text="समुदायिक बन उपभोक्ता प्रतिनिधि (नाम)")
    community_representative_sign_date = models.DateField(
        null=True, blank=True, help_text="समुदायिक बन उपभोक्ता प्रतिनिधि दस्तखत (मिति)"
    )

    forest_officer = models.CharField(max_length=255, blank=True, help_text="वन प्रतिनिधि (नाम)")
    forest_officer_sign_date = models.DateField(null=True, blank=True, help_text="वन प्रतिनिधि दस्तखत (मिति)")

    notes = models.TextField(blank=True, help_text="Additional remarks")

    class Meta:
        ordering = ["-survey_date", "block"]
        verbose_name = "Tree Survey Form"
        verbose_name_plural = "Tree Survey Forms"

    def __str__(self) -> str:
        return f"Form {self.form_number} - {self.block.block_name} - {self.survey_date}"

    def get_total_volume(self) -> float:
        """Get total wood volume for this form"""
        return sum(float(item.volume_cubic_m or 0) for item in self.tree_items.all())

    def get_total_fuelwood(self) -> float:
        """Get total fuelwood volume"""
        return sum(float(item.fuelwood_volume_cubic_m or 0) for item in self.tree_items.all())


class TreeSurveyFormItem(AbstractBaseModel):
    """Individual tree/wood entry in survey form"""

    survey_form = models.ForeignKey(TreeSurveyForm, on_delete=models.CASCADE, related_name="tree_items")

    # Entry number
    serial_number = models.PositiveIntegerField(help_text="क्र.स.")

    # Wood/tree information
    species = models.ForeignKey(Species, on_delete=models.PROTECT, help_text="खान्चको नाम (Species name)")

    # Measurements
    girth_cm = models.DecimalField(
        max_digits=6, decimal_places=1, validators=[MinValueValidator(0)], help_text="गोलाई न. (Girth in cm)"
    )
    height_m = models.DecimalField(
        max_digits=5, decimal_places=1, validators=[MinValueValidator(0)], help_text="लाइड (Height in m)"
    )

    # Volume calculations
    volume_cubic_m = models.DecimalField(
        max_digits=10, decimal_places=3, validators=[MinValueValidator(0)], help_text="आयतन (Volume in cubic meter)"
    )

    fuelwood_volume_cubic_m = models.DecimalField(
        max_digits=10, decimal_places=3, validators=[MinValueValidator(0)], default=0, help_text="छोटिकरन (Fuelwood volume)"
    )

    # Classification
    wood_type = models.CharField(
        max_length=50,
        help_text="इस्पात निकासको किसिम (Wood type)",
        choices=[
            ("timber", "काठ"),
            ("fuelwood", "दाउरा"),
            ("other", "अन्य"),
        ],
    )

    remarks = models.TextField(blank=True, help_text="टिप्पणी")

    class Meta:
        ordering = ["survey_form", "serial_number"]
        verbose_name = "Tree Survey Form Item"
        verbose_name_plural = "Tree Survey Form Items"
        unique_together = [["survey_form", "serial_number"]]

    def __str__(self) -> str:
        return f"{self.survey_form.form_number} - #{self.serial_number} - {self.species.species_name}"


class CuttingRegister(AbstractBaseModel):
    """Cutting/Ghaat Register form (अनुसूची-८ घाटागीरो/कटान रजिस्टर)"""

    # Form metadata
    form_number = models.CharField(max_length=50, unique=True, help_text="Form identification number (पूर्जी क्र.स.)")
    register_date = models.DateField(help_text="Date of register (मिति)")

    # Forest information
    block = models.ForeignKey(ForestBlock, on_delete=models.PROTECT, related_name="cutting_registers", null=True, blank=True)
    operational_plan = models.ForeignKey(
        OperationalPlan, on_delete=models.PROTECT, null=True, blank=True, related_name="cutting_registers"
    )

    # Spatial information
    zone = models.CharField(max_length=255, help_text="क्षेत्र (Zone)")
    district = models.CharField(max_length=255, help_text="जिल्ला (District)")
    municipality = models.CharField(max_length=255, help_text="गाउँपालिका / नगरपालिका")
    ward_number = models.PositiveIntegerField(help_text="वार्ड नं.")

    # Forest classification
    forest_classification = models.CharField(max_length=255, blank=True, help_text="वन-क्षिजिञयात (Forest Classification)")

    # Block/Plot information
    block_plot_name = models.CharField(max_length=255, help_text="खण्ड/प्लटको नाम (Block/Plot name)")
    block_plot_type = models.CharField(max_length=255, blank=True, help_text="खण्ड/प्लटको किसिम (Type)")

    # Cutting location
    cutting_location = models.CharField(max_length=255, help_text="घाटागीरोको स्थान (Cutting location)")

    # Community representative information
    community_representative_name = models.CharField(
        max_length=255, blank=True, help_text="सामुदायिक वनको प्रतिनिधि नाम (Name)"
    )
    community_representative_position = models.CharField(
        max_length=255, blank=True, help_text="सामुदायिक वनको प्रतिनिधि पद (Position)"
    )
    community_representative_sign_date = models.DateField(
        null=True, blank=True, help_text="सामुदायिक वनको प्रतिनिधि दस्तखत मिति (Date)"
    )

    # Forest officer information
    forest_officer_name = models.CharField(max_length=255, blank=True, help_text="वन प्रतिनिधि नाम (Name)")
    forest_officer_position = models.CharField(max_length=255, blank=True, help_text="वन प्रतिनिधि पद (Position)")
    forest_officer_sign_date = models.DateField(null=True, blank=True, help_text="वन प्रतिनिधि दस्तखत मिति (Date)")

    notes = models.TextField(blank=True, help_text="Additional remarks")

    class Meta:
        ordering = ["-register_date", "block"]
        verbose_name = "Cutting Register"
        verbose_name_plural = "Cutting Registers"

    def __str__(self) -> str:
        return f"Cutting Register {self.form_number} - {self.block.block_name} - {self.register_date}"

    def get_total_volume(self) -> float:
        """Get total volume for this register"""
        return sum(float(item.volume_cubic_m or 0) for item in self.cutting_items.all())

    def get_item_count(self) -> int:
        """Get total number of items"""
        return self.cutting_items.count()


class CuttingRegisterItem(AbstractBaseModel):
    """Individual cutting entry in cutting register"""

    cutting_register = models.ForeignKey(CuttingRegister, on_delete=models.CASCADE, related_name="cutting_items")

    # Entry number
    serial_number = models.PositiveIntegerField(help_text="मिमिट (Serial number)")

    # Time entry
    entry_time = models.TimeField(null=True, blank=True, help_text="समय (Time)")

    # Plot information
    plot_number = models.CharField(max_length=50, help_text="रमाना न. (Plot number)")
    quota_number = models.CharField(max_length=50, blank=True, help_text="गोपिया न. (Quota/License number)")

    # Species and wood information
    species = models.ForeignKey(Species, on_delete=models.PROTECT, help_text="जात (Species name)")

    # Measurements
    size_measurement = models.CharField(max_length=255, help_text="नाप साइज (Size/Measurement)")
    volume_cubic_m = models.DecimalField(
        max_digits=10, decimal_places=3, validators=[MinValueValidator(0)], help_text="आयतन (Volume in cubic meter)"
    )

    # Additional notes
    comments = models.CharField(max_length=500, blank=True, help_text="दादुरा (Comments)")
    remarks = models.TextField(blank=True, help_text="कैफियत (Remarks)")

    class Meta:
        ordering = ["cutting_register", "serial_number"]
        verbose_name = "Cutting Register Item"
        verbose_name_plural = "Cutting Register Items"
        unique_together = [["cutting_register", "serial_number"]]

    def __str__(self) -> str:
        return f"{self.cutting_register.form_number} - #{self.serial_number} - {self.species.species_name}"


class FellingRegister(AbstractBaseModel):
    """
    Header of a single Anusuchi-8 register: site/agency details, deadlines,
    and the two signatories (CFUG representative + Forest Office representative).
    """

    # क्षेत्र / जिल्ला / सब-डिभिजन / खण्ड
    area = models.CharField("Area (क्षेत्र)", max_length=255, blank=True)
    district = models.CharField("District (जिल्ला)", max_length=255, blank=True)
    sub_division = models.CharField("Sub-division (सब-डिभिजन)", max_length=255, blank=True)
    block_name_and_type = models.CharField("Block/Plot name & type (खण्ड/प्लटको नाम र किसिम)", max_length=255, blank=True)
    felling_location = models.CharField("Felling location (घाटगद्दीको स्थान)", max_length=255, blank=True)

    # कटान गर्ने निकायको विवरण
    cutting_agency_name = models.CharField("Cutting agency name (कटान गर्ने निकायको नाम)", max_length=255, blank=True)
    tree_count = models.PositiveIntegerField("Tree count (रुख संख्या)", null=True, blank=True)
    felling_sawing_deadline = models.DateField("Felling/sawing deadline (कटान चिरान म्याद)", null=True, blank=True)
    dispatch_deadline = models.DateField("Dispatch deadline (निकासी म्याद)", null=True, blank=True)

    # सामुदायिक वनको प्रतिनिधि (CFUG representative)
    cfug_rep_name = models.CharField("CFUG rep. name (नाम)", max_length=255, blank=True)
    cfug_rep_position = models.CharField("CFUG rep. position (पद)", max_length=255, blank=True)
    cfug_rep_signed_date = models.DateField("CFUG rep. signed date (मिति)", null=True, blank=True)

    # वन प्रतिनिधि (Forest Office representative)
    forest_rep_name = models.CharField("Forest rep. name (नाम)", max_length=255, blank=True)
    forest_rep_position = models.CharField("Forest rep. position (पद)", max_length=255, blank=True)
    forest_rep_signed_date = models.DateField("Forest rep. signed date (मिति)", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Felling Register (Anusuchi-8)"
        verbose_name_plural = "Felling Registers (Anusuchi-8)"

    def __str__(self):
        return f"Felling Register #{self.pk} — {self.felling_location or self.block_name_and_type or 'Untitled'}"


class FellingRegisterEntry(AbstractBaseModel):
    """
    One row of the घाटगद्दी/कटान table: a single tree/log/lot that was
    measured and recorded on a given date.
    """

    register = models.ForeignKey(FellingRegister, on_delete=models.CASCADE, related_name="entries")

    entry_date = models.DateField("Date (मिति)", null=True, blank=True)
    entry_time = models.TimeField("Time (समय)", null=True, blank=True)
    rawana_number = models.CharField("Rawana / transit permit no. (रमाना नं.)", max_length=100, blank=True)
    golia_number = models.CharField("Log / golia no. (गोलिया नं.)", max_length=100, blank=True)
    species = models.ForeignKey(
        Species,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="felling_register_entries",
    )
    measurement_size = models.CharField("Measurement / size (नाप साइज)", max_length=255, blank=True)
    volume_cubic_feet = models.DecimalField(
        "Volume in cu.ft. (आयतन क्यू.फि.)",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    firewood_chatta = models.DecimalField(
        "Firewood in chatta (दाउरा चट्टा)",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    remarks = models.TextField("Remarks (कैफियत)", blank=True)

    class Meta:
        ordering = ["entry_date", "entry_time", "id"]
        verbose_name = "Felling Register Entry"
        verbose_name_plural = "Felling Register Entries"

    def __str__(self):
        return f"Entry #{self.pk} for register #{self.register_id}"


class ForestProductReceipt(AbstractBaseModel):
    """
    अनुसुचि-१० — Forest Product Sales Distribution Receipt
    Forest Regulation 2079, Rule 49, Sub-rule (1) and (3)
    """

    # Header
    receipt_no = models.CharField(max_length=64, unique=True)
    cfug_registration_no = models.CharField(max_length=64, blank=True, help_text="उपभोक्ता समूहको दर्ता नं.")
    buyer_name = models.CharField(max_length=255, help_text="श्री — recipient's full name")
    buyer_address = models.CharField(max_length=255, blank=True)
    issue_date = models.DateField()

    # Optional FK to your existing Sale records
    # One receipt can consolidate multiple sales
    sales = models.ManyToManyField(
        Sale,
        blank=True,
        related_name="product_receipts",
    )

    # Footer — receiver (रांसद बुभ्फ लिनेको)
    receiver_name = models.CharField(max_length=255, blank=True)
    receiver_date = models.DateField(null=True, blank=True)

    # Footer — issuer (रांसद दिनेको)
    issuer_name = models.CharField(max_length=255, blank=True)
    issuer_position = models.CharField(max_length=128, blank=True)
    issuer_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-issue_date", "-receipt_no"]
        verbose_name = "Forest Product Receipt"
        verbose_name_plural = "Forest Product Receipts"

    def __str__(self) -> str:
        return f"Receipt {self.receipt_no} — {self.buyer_name}"

    @property
    def grand_total(self):
        from django.db.models import Sum

        result = self.items.aggregate(total=Sum("total_amount"))
        return result["total"] or 0


class ForestProductReceiptItem(AbstractBaseModel):
    """
    One row in the receipt table.
    """

    receipt = models.ForeignKey(
        ForestProductReceipt,
        on_delete=models.CASCADE,
        related_name="items",
    )
    # वनपैदावारको नाम र जात
    product_name = models.CharField(max_length=255)
    grade = models.CharField(max_length=64, blank=True)
    # ईकाई
    unit = models.CharField(max_length=32)
    # परिमाण
    quantity = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    # Rate used (for audit; not shown on receipt)
    rate_per_unit = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    # कूल रकम — auto-calculated on save
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    # कैफियत
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "Receipt Item"
        verbose_name_plural = "Receipt Items"

    def __str__(self) -> str:
        return f"{self.product_name} x {self.quantity}"

    def save(self, *args, **kwargs):
        self.total_amount = self.quantity * self.rate_per_unit
        super().save(*args, **kwargs)
