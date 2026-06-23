from __future__ import annotations

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import AbstractBaseModel


class ForestBlock(AbstractBaseModel):
    block_name = models.CharField(max_length=255)
    area_hectares = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        ordering = ["block_name"]
        verbose_name = "Forest Block"
        verbose_name_plural = "Forest Blocks"

    def __str__(self) -> str:
        return self.block_name


class Species(AbstractBaseModel):
    species_name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ["species_name"]
        verbose_name = "Species"
        verbose_name_plural = "Species"

    def __str__(self) -> str:
        return self.species_name


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
    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name="tree_counts")
    block = models.ForeignKey(
        ForestBlock,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tree_counts",
    )
    total_count = models.PositiveIntegerField(
        validators=[MinValueValidator(0)], help_text="Baseline tree count from inventory"
    )
    harvested_count = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    adjustment_reason = models.TextField(
        blank=True,
        help_text="Reason for any manual adjustment to the baseline total_count",
    )

    class Meta:
        ordering = ["species__species_name", "block__block_name"]
        verbose_name = "Tree Count Register"
        verbose_name_plural = "Tree Count Register"
        constraints = [models.UniqueConstraint(fields=["species", "block"], name="unique_species_block_tree_count")]

    def __str__(self) -> str:
        block = self.block.block_name if self.block else "All blocks"
        return f"{self.species.species_name} - {block}"

    @property
    def remaining_count(self) -> int:
        return max(0, self.total_count - self.harvested_count)


class TreeCountHistory(AbstractBaseModel):
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
