from rest_framework import serializers

from apps.forest.models import (
    ForestBlock,
    OperationalPlan,
    Species,
    TreeCountHistory,
    TreeCountRegister,
)


class ForestBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForestBlock
        fields = ["id", "block_name", "area_hectares", "created_at", "updated_at"]


class SpeciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Species
        fields = ["id", "species_name", "created_at", "updated_at"]


class OperationalPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationalPlan
        fields = [
            "id",
            "valid_from",
            "valid_to",
            "approved_harvest_limit",
            "description",
            "created_at",
            "updated_at",
        ]


class TreeCountHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TreeCountHistory
        fields = [
            "id",
            "record",
            "change_amount",
            "reference_harvest",
            "change_date",
            "note",
            "created_at",
        ]


class TreeCountRegisterSerializer(serializers.ModelSerializer):
    remaining_count = serializers.IntegerField(read_only=True)
    species_name = serializers.CharField(source="species.species_name", read_only=True)
    block_name = serializers.CharField(source="block.block_name", read_only=True, allow_null=True)

    class Meta:
        model = TreeCountRegister
        fields = [
            "id",
            "species",
            "species_name",
            "block",
            "block_name",
            "total_count",
            "harvested_count",
            "remaining_count",
            "last_updated",
            "adjustment_reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["harvested_count"]
