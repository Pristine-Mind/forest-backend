from decimal import Decimal

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.inventory.models import StockLedger, StockTransaction, TimberLogEntry


@receiver(post_save, sender=TimberLogEntry)
def create_stock_transaction_for_timber_harvest(sender, instance, created, **kwargs):
    """
    Create a StockTransaction when a TimberLogEntry is created with volume_cubic_feet.
    Logs the harvest as an IN transaction for inventory tracking.
    """
    if instance.volume_cubic_feet and instance.volume_cubic_feet > 0:
        # Get or create StockLedger for this species and grade
        stock_ledger, _ = StockLedger.objects.get_or_create(
            species=instance.species,
            grade=instance.grade,
        )

        # Create StockTransaction for the harvest
        StockTransaction.objects.create(
            stock=stock_ledger,
            transaction_type=StockTransaction.Type.IN,
            quantity=Decimal(str(instance.volume_cubic_feet)),
            reference_type=StockTransaction.ReferenceType.HARVEST,
            reference_id=instance.id,
            note=f"Harvest from tree {instance.tree_no}, log {instance.golia_no}",
        )
