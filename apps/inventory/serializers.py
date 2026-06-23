from rest_framework import serializers

from apps.inventory.models import PriceRate, Sale, StockLedger, StockTransaction


class StockTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockTransaction
        fields = [
            "id",
            "stock",
            "transaction_type",
            "quantity",
            "reference_type",
            "reference_id",
            "note",
            "created_at",
        ]
        read_only_fields = ["reference_type", "reference_id"]


class StockLedgerSerializer(serializers.ModelSerializer):
    quantity_available = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    species_name = serializers.CharField(source="species.species_name", read_only=True)

    class Meta:
        model = StockLedger
        fields = [
            "id",
            "species",
            "species_name",
            "grade",
            "quantity_available",
            "created_at",
            "updated_at",
        ]


class PriceRateSerializer(serializers.ModelSerializer):
    species_name = serializers.CharField(source="species.species_name", read_only=True)

    class Meta:
        model = PriceRate
        fields = [
            "id",
            "species",
            "species_name",
            "grade",
            "buyer_type",
            "rate_per_unit",
            "effective_from",
            "created_at",
            "updated_at",
        ]


class SaleSerializer(serializers.ModelSerializer):
    species_name = serializers.CharField(source="species.species_name", read_only=True)
    member_name = serializers.CharField(source="member.full_name", read_only=True, allow_null=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Sale
        fields = [
            "id",
            "buyer_name",
            "buyer_type",
            "member",
            "member_name",
            "species",
            "species_name",
            "grade",
            "quantity",
            "rate_applied",
            "total_amount",
            "payment_status",
            "receipt_no",
            "audit_note",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["receipt_no", "total_amount"]

    def validate(self, attrs):
        buyer_type = attrs.get("buyer_type")
        member = attrs.get("member")
        if buyer_type == Sale.BuyerType.MEMBER and not member:
            raise serializers.ValidationError({"member": "Member is required when buyer type is member."})
        if buyer_type == Sale.BuyerType.OUTSIDER and member:
            raise serializers.ValidationError({"member": "Member must be blank when buyer type is outsider."})
        return attrs
