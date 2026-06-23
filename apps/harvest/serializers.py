from rest_framework import serializers

from apps.harvest.models import HarvestRequest


class HarvestRequestSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.full_name", read_only=True)
    species_name = serializers.CharField(source="species.species_name", read_only=True)
    approved_by_name = serializers.CharField(source="approved_by.full_name", read_only=True)

    class Meta:
        model = HarvestRequest
        fields = [
            "id",
            "source_type",
            "member",
            "member_name",
            "operation_name",
            "species",
            "species_name",
            "quantity",
            "status",
            "requested_date",
            "approved_by",
            "approved_by_name",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["status", "approved_by"]

    def validate(self, attrs):
        source_type = attrs.get("source_type", self.instance.source_type if self.instance else None)
        member = attrs.get("member", getattr(self.instance, "member", None) if self.instance else None)
        operation_name = attrs.get("operation_name", getattr(self.instance, "operation_name", "") if self.instance else "")

        if source_type == HarvestRequest.SourceType.MEMBER_REQUESTED:
            if not member:
                raise serializers.ValidationError({"member": "Member is required for member-requested harvests."})
            if member.membership_status != member.MembershipStatus.ACTIVE:
                raise serializers.ValidationError({"member": "Only active members may submit a harvest request."})
            if operation_name:
                raise serializers.ValidationError({"operation_name": "Must be blank for member-requested harvests."})
        elif source_type == HarvestRequest.SourceType.FOREST_INITIATED:
            if member:
                raise serializers.ValidationError({"member": "Must be blank for forest-initiated harvests."})
            if not operation_name:
                raise serializers.ValidationError(
                    {"operation_name": "Operation name is required for forest-initiated harvests."}
                )

        status = attrs.get(
            "status",
            (
                getattr(self.instance, "status", HarvestRequest.Status.PENDING)
                if self.instance
                else HarvestRequest.Status.PENDING
            ),
        )
        notes = attrs.get("notes", getattr(self.instance, "notes", "") if self.instance else "")
        if status == HarvestRequest.Status.REJECTED and not notes:
            raise serializers.ValidationError({"notes": "Notes are required when rejecting a request."})

        return attrs
