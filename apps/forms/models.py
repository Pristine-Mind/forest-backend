from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import AbstractBaseModel
from apps.forest.models import ForestBlock, OperationalPlan, Species


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
