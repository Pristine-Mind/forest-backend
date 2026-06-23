from rest_framework import serializers

from apps.visitors.models import OfficialGuestLog, VisitorEntry, VisitorFeeRate


class VisitorFeeRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitorFeeRate
        fields = [
            "id",
            "visit_purpose",
            "fee_per_visitor_per_day",
            "created_at",
            "updated_at",
        ]


class VisitorEntrySerializer(serializers.ModelSerializer):
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = VisitorEntry
        fields = [
            "id",
            "entry_date",
            "visit_purpose",
            "visitor_count",
            "days",
            "fee_waived",
            "total_amount",
            "receipt_no",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["receipt_no", "total_amount"]


class OfficialGuestLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfficialGuestLog
        fields = [
            "id",
            "visitor_name",
            "designation",
            "visit_start_date",
            "visit_end_date",
            "comments_or_guidance",
            "created_at",
            "updated_at",
        ]
