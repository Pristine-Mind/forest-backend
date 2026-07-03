from __future__ import annotations

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import AbstractBaseModel


class ForestBlock(AbstractBaseModel):
    block_no = models.PositiveIntegerField(unique=True, help_text="Block number", verbose_name="Block number (ब्लक नं.)")
    block_name = models.CharField(max_length=255, help_text="Block name (नाम)", verbose_name="Block name (नाम)")
    title = models.CharField(
        max_length=500, blank=True, help_text="Block title/description", verbose_name="Block title/description (शीर्षक/विवरण)"
    )

    # Area information
    total_area_ha = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Total area in hectares (कुल क्षेत्रफल हेक्टेयरमा)",
        verbose_name="Total area in hectares (कुल क्षेत्रफल हेक्टेयरमा)",
    )
    productive_area_ha = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text="Productive area in hectares (उत्पादक क्षेत्रफल)",
        verbose_name="Productive area in hectares (उत्पादक क्षेत्रफल)",
    )
    canopy_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text="Canopy coverage percentage (छत्र आच्छादन प्रतिशत)",
        verbose_name="Canopy coverage percentage (छत्र आच्छादन प्रतिशत)",
    )

    # Soil types (stored as JSON array)
    soil_types = models.JSONField(
        default=list, blank=True, help_text="Soil types (माटोको प्रकार)", verbose_name="Soil types (माटोको प्रकार)"
    )

    # Forest information
    forest_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="Forest type (वन प्रकार - प्राकृतिक/रोपित)",
        verbose_name="Forest type (वन प्रकार - प्राकृतिक/रोपित)",
    )
    forest_condition = models.CharField(
        max_length=100, blank=True, help_text="Forest condition (वन अवस्था)", verbose_name="Forest condition (वन अवस्था)"
    )

    # Major species (stored as JSON array)
    major_species = models.JSONField(
        default=list,
        blank=True,
        help_text="Major tree species (प्रमुख वृक्ष प्रजातिहरु)",
        verbose_name="Major tree species (प्रमुख वृक्ष प्रजातिहरु)",
    )

    # Management activities (stored as JSON array)
    forest_management_activities = models.JSONField(
        default=list, blank=True, help_text="Forest management activities (वन व्यवस्थापन गतिविधिहरु)"
    )

    # Non-timber forest products (stored as JSON array)
    non_timber_forest_products = models.JSONField(
        default=list, blank=True, help_text="Non-timber forest products (गैर-काठ वन उत्पादनहरु)"
    )

    # Wildlife (stored as JSON array)
    wildlife_species = models.JSONField(
        default=list, blank=True, help_text="Wildlife species found in block (वन्यजन्तु प्रजातिहरु)"
    )

    # Boundaries (stored as JSON object)
    boundaries = models.JSONField(
        default=dict, blank=True, help_text="Block boundaries - {east, west, north, south} (सीमानाहरु)"
    )

    class Meta:
        ordering = ["block_no"]
        verbose_name = "Forest Block"
        verbose_name_plural = "Forest Blocks"

    def __str__(self) -> str:
        return f"Block {self.block_no} - {self.block_name}"


class Species(AbstractBaseModel):
    species_name = models.CharField(max_length=255, unique=True)
    scientific_name = models.CharField(max_length=255, blank=True)
    local_name = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["species_name"]
        verbose_name = "Species"
        verbose_name_plural = "Species"

    def __str__(self) -> str:
        return self.species_name


class WildlifeSpecies(AbstractBaseModel):
    species_name = models.CharField(max_length=255, unique=True)
    scientific_name = models.CharField(max_length=255, blank=True)
    local_name = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["species_name"]
        verbose_name = "Wildlife Species"
        verbose_name_plural = "Wildlife Species"

    def __str__(self) -> str:
        return self.species_name


class TimberCollection(AbstractBaseModel):
    block = models.ForeignKey(ForestBlock, on_delete=models.CASCADE, related_name="collections")
    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name="collections")
    wood_volume = models.DecimalField(max_digits=12, decimal_places=2, help_text="घन फिट")

    firewood = models.DecimalField(max_digits=10, decimal_places=2, help_text="चट्टा")

    class Meta:
        unique_together = ("block", "species")
        ordering = ["block", "species"]

    def __str__(self):
        return f"{self.block} - {self.species}"


class OperationalPlan(AbstractBaseModel):
    valid_from = models.DateField()
    valid_to = models.DateField()
    approved_harvest_limit = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-valid_from"]
        verbose_name = "Operational Plan"
        verbose_name_plural = "Operational Plans"

    def __str__(self) -> str:
        return f"Plan {self.valid_from} to {self.valid_to}"


class TreeCountRegister(AbstractBaseModel):
    """Flat model for tree inventory data - each row represents a tree measurement"""

    # Relationships
    block = models.ForeignKey(ForestBlock, on_delete=models.CASCADE, null=True, blank=True, related_name="tree_registers")
    operational_plan = models.ForeignKey(
        OperationalPlan, null=True, blank=True, on_delete=models.CASCADE, related_name="tree_registers"
    )
    species = models.ForeignKey(Species, null=True, blank=True, on_delete=models.CASCADE, related_name="tree_registers")

    # Plot information
    plot_number = models.PositiveIntegerField(help_text="Plot number (प्लट नं)", null=True, blank=True)
    tree_number = models.PositiveIntegerField(help_text="Tree sequence number in plot (क्र.स.)", null=True, blank=True)

    # Tree measurements
    girth_cm = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Girth at breast height in cm (गोलाई)",
    )
    height_m = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Tree height in meters (उचाई)",
    )

    # Tree classification
    tree_class = models.CharField(
        max_length=10,
        choices=[
            ("i", "I"),
            ("ii", "II"),
            ("iii", "III"),
        ],
        null=True,
        blank=True,
        help_text="Tree class/category (श्रेणी)",
    )

    # Calculated volume fields
    basal_area_sqm = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text="Basal area in sq meters (बेसल एरिआ वगा मि.)",
    )
    stem_volume_cubic_m = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Stem volume in cubic meters (काण्डको आयतन)",
    )

    # R factor and branch volume
    r_factor = models.DecimalField(
        max_digits=4, decimal_places=2, default=0.00, help_text="R factor for branch volume calculation"
    )
    branch_volume_cubic_m = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Branch volume in cubic meters (हाँगाको आयतन)",
    )
    total_volume_cubic_m = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Total tree volume in cubic meters (रुखको आयतन)",
    )

    # Small diameter volumes (R < 10cm)
    r_less_than_10 = models.DecimalField(
        max_digits=4, decimal_places=2, default=0.00, help_text="R factor for <10cm diameter"
    )
    volume_less_than_10_cubic_m = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Volume for <10cm diameter",
    )

    # Final volume calculations
    gross_volume_cubic_m = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Gross volume in cubic meters (ग्रस आयतन)",
    )
    net_volume_cubic_m = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Net volume in cubic meters (नेट आयतन घ.मि.)",
    )
    fuelwood_volume_cubic_m = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Fuelwood volume in cubic meters (दाउरा जम्मा आयतन घ.मि.)",
    )

    # Additional metadata
    survey_date = models.DateField(null=True, blank=True, help_text="Date of survey/measurement")
    is_harvestable = models.BooleanField(default=True, help_text="Whether this tree can be harvested")
    is_active = models.BooleanField(default=True, help_text="Whether this record is active or archived")
    notes = models.TextField(blank=True, help_text="Additional notes for this tree record")

    class Meta:
        ordering = ["block__block_name", "plot_number", "tree_number"]
        verbose_name = "Tree Count Register"
        verbose_name_plural = "Tree Count Register"
        unique_together = [
            ["block", "plot_number", "tree_number"],
            ["block", "operational_plan", "species", "tree_number"],
        ]
        indexes = [
            models.Index(fields=["block", "plot_number"]),
            models.Index(fields=["species"]),
            models.Index(fields=["operational_plan"]),
        ]

    def __str__(self) -> str:
        return f"{self.block.block_name} - Plot {self.plot_number} - Tree #{self.tree_number} - {self.species.species_name}"

    def save(self, *args, **kwargs):
        """Calculate derived fields before saving"""
        # Calculate derived fields only if girth_cm is provided and valid
        if self.girth_cm is not None and self.girth_cm > 0 and self.height_m is not None and self.height_m > 0:
            # Calculate Basal Area: π * (DBH/2)^2 where DBH = girth/π
            pi = Decimal("3.14159")
            dbh = self.girth_cm / pi  # Diameter at breast height
            self.basal_area_sqm = pi * ((dbh / Decimal("200")) ** 2)  # Convert cm to meters

            # Stem Volume = Basal Area * Height * Form Factor (0.45 for Sal)
            form_factor = Decimal("0.45")
            self.stem_volume_cubic_m = self.basal_area_sqm * self.height_m * form_factor

            # R factor based on tree class
            class_r_factors = {
                "i": Decimal("0.00"),
                "ii": Decimal("0.15"),
                "iii": Decimal("0.30"),
            }
            self.r_factor = class_r_factors.get(self.tree_class, Decimal("0.00"))

            # Branch Volume = Stem Volume * R Factor
            self.branch_volume_cubic_m = self.stem_volume_cubic_m * self.r_factor

            # Total Volume = Stem Volume + Branch Volume
            self.total_volume_cubic_m = self.stem_volume_cubic_m + self.branch_volume_cubic_m

            # For trees with diameter < 10cm
            if dbh < Decimal("10"):
                self.r_less_than_10 = Decimal("0.02")
                self.volume_less_than_10_cubic_m = self.stem_volume_cubic_m * self.r_less_than_10
            else:
                self.r_less_than_10 = Decimal("0.00")
                self.volume_less_than_10_cubic_m = Decimal("0")

            # Gross Volume (removing bark loss factor - 5%)
            bark_loss_factor = Decimal("0.95")
            self.gross_volume_cubic_m = self.total_volume_cubic_m * bark_loss_factor

            # Net Volume (removing waste factor - 20%)
            waste_factor = Decimal("0.80")
            self.net_volume_cubic_m = self.gross_volume_cubic_m * waste_factor

            # Fuelwood Volume (from small branches and waste - 35%)
            fuelwood_factor = Decimal("0.35")
            self.fuelwood_volume_cubic_m = self.gross_volume_cubic_m * fuelwood_factor

        super().save(*args, **kwargs)

    @classmethod
    def get_plot_summary(cls, block_id, plot_number):
        """Get summary statistics for a specific plot"""
        trees = cls.objects.filter(block_id=block_id, plot_number=plot_number, is_active=True)

        if not trees.exists():
            return None

        return {
            "total_trees": trees.count(),
            "total_volume": trees.aggregate(models.Sum("total_volume_cubic_m"))["total_volume_cubic_m__sum"] or 0,
            "total_net_volume": trees.aggregate(models.Sum("net_volume_cubic_m"))["net_volume_cubic_m__sum"] or 0,
            "total_fuelwood": trees.aggregate(models.Sum("fuelwood_volume_cubic_m"))["fuelwood_volume_cubic_m__sum"] or 0,
            "species_count": trees.values("species__species_name").distinct().count(),
            "average_height": trees.aggregate(models.Avg("height_m"))["height_m__avg"] or 0,
            "average_girth": trees.aggregate(models.Avg("girth_cm"))["girth_cm__avg"] or 0,
        }

    @classmethod
    def get_block_summary(cls, block_id, operational_plan_id=None):
        """Get summary statistics for a block"""
        trees = cls.objects.filter(block_id=block_id, is_active=True)

        if operational_plan_id:
            trees = trees.filter(operational_plan_id=operational_plan_id)

        if not trees.exists():
            return None

        return {
            "total_trees": trees.count(),
            "total_plots": trees.values("plot_number").distinct().count(),
            "total_volume": trees.aggregate(models.Sum("total_volume_cubic_m"))["total_volume_cubic_m__sum"] or 0,
            "total_net_volume": trees.aggregate(models.Sum("net_volume_cubic_m"))["net_volume_cubic_m__sum"] or 0,
            "total_fuelwood": trees.aggregate(models.Sum("fuelwood_volume_cubic_m"))["fuelwood_volume_cubic_m__sum"] or 0,
            "species_list": trees.values_list("species__species_name", flat=True).distinct(),
            "average_height": trees.aggregate(models.Avg("height_m"))["height_m__avg"] or 0,
            "average_girth": trees.aggregate(models.Avg("girth_cm"))["girth_cm__avg"] or 0,
        }


class HarvestLog(AbstractBaseModel):
    """Track harvested trees from the register"""

    tree_record = models.ForeignKey(TreeCountRegister, on_delete=models.PROTECT, related_name="harvest_logs")
    harvest_date = models.DateField()
    harvest_quantity_cubic_m = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0)])
    reference_harvest_request = models.ForeignKey(
        "harvest.HarvestRequest", on_delete=models.SET_NULL, null=True, blank=True, related_name="harvest_logs"
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-harvest_date"]
        verbose_name = "Harvest Log"
        verbose_name_plural = "Harvest Logs"

    def __str__(self) -> str:
        return f"Harvest - {self.tree_record} - {self.harvest_date}"


class TreeCountHistory(AbstractBaseModel):
    """Historical tracking of tree count changes"""

    record = models.ForeignKey(TreeCountRegister, on_delete=models.CASCADE, related_name="history")
    change_amount = models.IntegerField(
        validators=[MinValueValidator(1)], help_text="Number of trees harvested in this change"
    )
    reference_harvest = models.ForeignKey(
        "harvest.HarvestRequest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tree_count_history",
    )
    change_date = models.DateField()
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-change_date"]
        verbose_name = "Tree Count History"
        verbose_name_plural = "Tree Count History"

    def __str__(self) -> str:
        return f"{self.record} - {self.change_amount} trees on {self.change_date}"


class PoleCountRegister(AbstractBaseModel):
    """Flat model for tree inventory data - each row represents a tree measurement"""

    # Relationships
    block = models.ForeignKey(ForestBlock, on_delete=models.CASCADE, null=True, blank=True, related_name="pole_registers")
    operational_plan = models.ForeignKey(
        OperationalPlan, null=True, blank=True, on_delete=models.CASCADE, related_name="pole_registers"
    )
    species = models.ForeignKey(Species, null=True, blank=True, on_delete=models.CASCADE, related_name="pole_registers")

    # Plot information
    plot_number = models.PositiveIntegerField(help_text="Plot number (प्लट नं)", null=True, blank=True)
    tree_number = models.PositiveIntegerField(help_text="Tree sequence number in plot (क्र.स.)", null=True, blank=True)

    # Tree measurements
    girth_cm = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Girth at breast height in cm (गोलाई)",
    )
    height_m = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Tree height in meters (उचाई)",
    )

    # Tree classification
    tree_class = models.CharField(
        max_length=10,
        choices=[
            ("i", "I"),
            ("ii", "II"),
            ("iii", "III"),
        ],
        null=True,
        blank=True,
        help_text="Tree class/category (श्रेणी)",
    )

    # Calculated volume fields
    basal_area_sqm = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text="Basal area in sq meters (बेसल एरिआ वगा मि.)",
    )
    stem_volume_cubic_m = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Stem volume in cubic meters (काण्डको आयतन)",
    )

    # R factor and branch volume
    r_factor = models.DecimalField(
        max_digits=4, decimal_places=2, default=0.00, help_text="R factor for branch volume calculation"
    )
    branch_volume_cubic_m = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Branch volume in cubic meters (हाँगाको आयतन)",
    )
    total_volume_cubic_m = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Total tree volume in cubic meters (रुखको आयतन)",
    )

    # Small diameter volumes (R < 10cm)
    r_less_than_10 = models.DecimalField(
        max_digits=4, decimal_places=2, default=0.00, help_text="R factor for <10cm diameter"
    )
    volume_less_than_10_cubic_m = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Volume for <10cm diameter",
    )

    # Final volume calculations
    gross_volume_cubic_m = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Gross volume in cubic meters (ग्रस आयतन)",
    )
    net_volume_cubic_m = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Net volume in cubic meters (नेट आयतन घ.मि.)",
    )
    fuelwood_volume_cubic_m = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Fuelwood volume in cubic meters (दाउरा जम्मा आयतन घ.मि.)",
    )

    # Additional metadata
    survey_date = models.DateField(null=True, blank=True, help_text="Date of survey/measurement")
    is_harvestable = models.BooleanField(default=True, help_text="Whether this tree can be harvested")
    is_active = models.BooleanField(default=True, help_text="Whether this record is active or archived")
    notes = models.TextField(blank=True, help_text="Additional notes for this tree record")

    class Meta:
        ordering = ["block__block_name", "plot_number", "tree_number"]
        verbose_name = "Tree Count Register"
        verbose_name_plural = "Tree Count Register"
        unique_together = [
            ["block", "plot_number", "tree_number"],
            ["block", "operational_plan", "species", "tree_number"],
        ]
        indexes = [
            models.Index(fields=["block", "plot_number"]),
            models.Index(fields=["species"]),
            models.Index(fields=["operational_plan"]),
        ]

    def __str__(self) -> str:
        return f"{self.block.block_name} - Plot {self.plot_number} - Tree #{self.tree_number} - {self.species.species_name}"

    def save(self, *args, **kwargs):
        """Calculate derived fields before saving"""
        # Calculate derived fields only if girth_cm is provided and valid
        if self.girth_cm is not None and self.girth_cm > 0 and self.height_m is not None and self.height_m > 0:
            # Calculate Basal Area: π * (DBH/2)^2 where DBH = girth/π
            pi = Decimal("3.14159")
            dbh = self.girth_cm / pi  # Diameter at breast height
            self.basal_area_sqm = pi * ((dbh / Decimal("200")) ** 2)  # Convert cm to meters

            # Stem Volume = Basal Area * Height * Form Factor (0.45 for Sal)
            form_factor = Decimal("0.45")
            self.stem_volume_cubic_m = self.basal_area_sqm * self.height_m * form_factor

            # R factor based on tree class
            class_r_factors = {
                "i": Decimal("0.00"),
                "ii": Decimal("0.15"),
                "iii": Decimal("0.30"),
            }
            self.r_factor = class_r_factors.get(self.tree_class, Decimal("0.00"))

            # Branch Volume = Stem Volume * R Factor
            self.branch_volume_cubic_m = self.stem_volume_cubic_m * self.r_factor

            # Total Volume = Stem Volume + Branch Volume
            self.total_volume_cubic_m = self.stem_volume_cubic_m + self.branch_volume_cubic_m

            # For trees with diameter < 10cm
            if dbh < Decimal("10"):
                self.r_less_than_10 = Decimal("0.02")
                self.volume_less_than_10_cubic_m = self.stem_volume_cubic_m * self.r_less_than_10
            else:
                self.r_less_than_10 = Decimal("0.00")
                self.volume_less_than_10_cubic_m = Decimal("0")

            # Gross Volume (removing bark loss factor - 5%)
            bark_loss_factor = Decimal("0.95")
            self.gross_volume_cubic_m = self.total_volume_cubic_m * bark_loss_factor

            # Net Volume (removing waste factor - 20%)
            waste_factor = Decimal("0.80")
            self.net_volume_cubic_m = self.gross_volume_cubic_m * waste_factor

            # Fuelwood Volume (from small branches and waste - 35%)
            fuelwood_factor = Decimal("0.35")
            self.fuelwood_volume_cubic_m = self.gross_volume_cubic_m * fuelwood_factor

        super().save(*args, **kwargs)

    @classmethod
    def get_plot_summary(cls, block_id, plot_number):
        """Get summary statistics for a specific plot"""
        trees = cls.objects.filter(block_id=block_id, plot_number=plot_number, is_active=True)

        if not trees.exists():
            return None

        return {
            "total_trees": trees.count(),
            "total_volume": trees.aggregate(models.Sum("total_volume_cubic_m"))["total_volume_cubic_m__sum"] or 0,
            "total_net_volume": trees.aggregate(models.Sum("net_volume_cubic_m"))["net_volume_cubic_m__sum"] or 0,
            "total_fuelwood": trees.aggregate(models.Sum("fuelwood_volume_cubic_m"))["fuelwood_volume_cubic_m__sum"] or 0,
            "species_count": trees.values("species__species_name").distinct().count(),
            "average_height": trees.aggregate(models.Avg("height_m"))["height_m__avg"] or 0,
            "average_girth": trees.aggregate(models.Avg("girth_cm"))["girth_cm__avg"] or 0,
        }

    @classmethod
    def get_block_summary(cls, block_id, operational_plan_id=None):
        """Get summary statistics for a block"""
        trees = cls.objects.filter(block_id=block_id, is_active=True)

        if operational_plan_id:
            trees = trees.filter(operational_plan_id=operational_plan_id)

        if not trees.exists():
            return None

        return {
            "total_trees": trees.count(),
            "total_plots": trees.values("plot_number").distinct().count(),
            "total_volume": trees.aggregate(models.Sum("total_volume_cubic_m"))["total_volume_cubic_m__sum"] or 0,
            "total_net_volume": trees.aggregate(models.Sum("net_volume_cubic_m"))["net_volume_cubic_m__sum"] or 0,
            "total_fuelwood": trees.aggregate(models.Sum("fuelwood_volume_cubic_m"))["fuelwood_volume_cubic_m__sum"] or 0,
            "species_list": trees.values_list("species__species_name", flat=True).distinct(),
            "average_height": trees.aggregate(models.Avg("height_m"))["height_m__avg"] or 0,
            "average_girth": trees.aggregate(models.Avg("girth_cm"))["girth_cm__avg"] or 0,
        }
