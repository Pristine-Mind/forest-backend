from rest_framework import serializers

from apps.billing.models import FeeCollection, Receipt


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
    payment_status = serializers.CharField(read_only=True)
    member_name = serializers.CharField(source="member.household_head_name", read_only=True, allow_null=True)

    class Meta:
        model = FeeCollection
        fields = [
            "id",
            "member",
            "member_name",
            "fee_type",
            "amount",
            "amount_paid",
            "payment_status",
            "receipt_no",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["receipt_no"]
