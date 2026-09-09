from datetime import date

from django.utils import timezone
from rest_framework import serializers

from apps.billing.models import FeeCollection, Receipt
from apps.billing.tasks import generate_receipt_pdf_task


class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = [
            "receipt_no",
            "reference_type",
            "reference_id",
            "amount",
            "issued_date",
            "issued_by",
            "pdf_file",
            "created_at",
        ]


class FeeCollectionSerializer(serializers.ModelSerializer):
    payment_status = serializers.SerializerMethodField()
    member_name = serializers.CharField(source="member.household_head_name", read_only=True, allow_null=True)
    receipt_no = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = FeeCollection
        fields = [
            "id",
            "member",
            "member_name",
            "fee_type",
            "amount",
            "quantity",
            "amount_paid",
            "payment_status",
            "receipt_no",
            "rate",
            "description",
            "remarks",
            "created_at",
            "updated_at",
        ]

    def get_payment_status(self, obj):
        """Dynamically calculate payment status."""
        if obj.amount_paid and obj.amount_paid >= obj.amount:
            return FeeCollection.PaymentStatus.PAID
        elif obj.amount_paid and obj.amount_paid > 0:
            return FeeCollection.PaymentStatus.PARTIAL
        return FeeCollection.PaymentStatus.DUE

    def create(self, validated_data):
        instance = FeeCollection.objects.create(**validated_data)
        # Check if payment is marked as paid/partial on creation
        amount_paid = validated_data.get("amount_paid", 0)
        if amount_paid and amount_paid > 0:
            self._create_receipt(instance)
        return instance

    def update(self, instance, validated_data):
        # Check if amount_paid changed and receipt needs to be created
        old_amount_paid = instance.amount_paid or 0
        new_amount_paid = validated_data.get("amount_paid", old_amount_paid)

        instance = super().update(instance, validated_data)

        # Create receipt if payment was made and it doesn't exist
        if new_amount_paid > 0 and not instance.receipt_no and old_amount_paid != new_amount_paid:
            self._create_receipt(instance)

        return instance

    def _create_receipt(self, fee_collection):
        """Create a receipt for the fee collection and trigger PDF generation."""
        if fee_collection.receipt_no:
            return  # Receipt already exists

        try:
            receipt = Receipt.objects.create(
                reference_type=Receipt.ReferenceType.FEE_COLLECTION,
                reference_id=fee_collection.id,
                amount=fee_collection.amount_paid or fee_collection.amount,
                issued_date=date.today(),
                issued_by=self.context.get("request").user if self.context.get("request") else None,
            )
            fee_collection.receipt_no = receipt
            fee_collection.save(update_fields=["receipt_no"])
            # Trigger PDF generation asynchronously
            generate_receipt_pdf_task.delay(receipt.receipt_no)
        except Exception as e:
            # Log error but don't fail the request
            print(f"Error creating receipt for FeeCollection {fee_collection.id}: {e}")
