from rest_framework import serializers

from apps.offense.models import (
    EvidenceItem,
    HearingRecord,
    InformantReward,
    OffenseReport,
    PatrolLog,
)


class EvidenceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenceItem
        fields = [
            "id",
            "offense",
            "item_type",
            "description",
            "confiscated_date",
            "created_at",
        ]


class HearingRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = HearingRecord
        fields = [
            "id",
            "offense",
            "accused_statement",
            "hearing_date",
            "outcome",
            "created_at",
        ]


class InformantRewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = InformantReward
        fields = [
            "id",
            "offense",
            "informant",
            "reward_amount",
            "paid_date",
            "created_at",
        ]


class OffenseReportSerializer(serializers.ModelSerializer):
    evidence_count = serializers.IntegerField(source="evidence.count", read_only=True)
    hearings_count = serializers.IntegerField(source="hearings.count", read_only=True)

    class Meta:
        model = OffenseReport
        fields = [
            "id",
            "reported_by",
            "accused_name",
            "offense_type",
            "description",
            "report_date",
            "status",
            "damage_value",
            "fine_amount",
            "resolution",
            "informant",
            "evidence_count",
            "hearings_count",
            "created_at",
            "updated_at",
        ]


class PatrolLogSerializer(serializers.ModelSerializer):
    watcher_name = serializers.CharField(source="watcher.full_name", read_only=True)

    class Meta:
        model = PatrolLog
        fields = [
            "id",
            "watcher",
            "watcher_name",
            "patrol_date",
            "notes",
            "offense",
            "created_at",
            "updated_at",
        ]
