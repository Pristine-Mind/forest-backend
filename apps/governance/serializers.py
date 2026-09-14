from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType

from apps.governance.models import (
    Candidate,
    CommitteeMember,
    Election,
    HandoverRecord,
    NoConfidenceMotion,
    OathRecord,
    SubCommittee,
)
from apps.members.models import Household, Member


class CommitteeMemberSerializer(serializers.ModelSerializer):
    member_name = serializers.SerializerMethodField()
    member_type = serializers.SerializerMethodField()
    subcommittee_names = serializers.SerializerMethodField()
    content_type = serializers.CharField(write_only=True, required=False)  # Accept string on write

    class Meta:
        model = CommitteeMember
        fields = [
            "id",
            "content_type",
            "object_id",
            "member_name",
            "member_type",
            "position",
            "gender",
            "caste_ethnicity",
            "term_start",
            "term_end",
            "status",
            "subcommittees",
            "subcommittee_names",
            "created_at",
            "updated_at",
            "photo",
        ]
        read_only_fields = ["id", "member_name", "member_type", "subcommittee_names", "created_at", "updated_at"]

    def get_member_name(self, obj):
        return obj.get_member_name()

    def get_member_type(self, obj):
        """Return 'household' or 'member'"""
        if obj.content_type:
            return obj.content_type.model
        return None

    def get_subcommittee_names(self, obj):
        return [sc.get_name_display() for sc in obj.subcommittees.all()]

    def _resolve_content_type(self, model_name):
        """
        Convert model name string ('household' or 'member') to ContentType ID.
        """
        model_map = {
            "household": Household,
            "member": Member,
        }

        model = model_map.get(model_name.lower())
        if not model:
            raise serializers.ValidationError(f"Invalid content_type: '{model_name}'. Must be 'household' or 'member'.")

        return ContentType.objects.get_for_model(model)

    def create(self, validated_data):
        """
        Handle content_type conversion from string to ContentType ID.
        """
        content_type_str = validated_data.pop("content_type", None)

        if content_type_str:
            content_type = self._resolve_content_type(content_type_str)
            validated_data["content_type"] = content_type

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Handle content_type conversion from string to ContentType ID.
        """
        content_type_str = validated_data.pop("content_type", None)

        if content_type_str:
            content_type = self._resolve_content_type(content_type_str)
            validated_data["content_type"] = content_type

        return super().update(instance, validated_data)


class CandidateSerializer(serializers.ModelSerializer):
    member_name = serializers.SerializerMethodField()

    class Meta:
        model = Candidate
        fields = [
            "id",
            "election",
            "member",
            "member_name",
            "position_applied",
            "votes_received",
            "result",
        ]

    def get_member_name(self, obj):
        """Get name from either Household or Member"""
        member = obj.member
        if hasattr(member, "household_head_name"):
            return member.household_head_name
        elif hasattr(member, "full_name"):
            return member.full_name
        return str(member)


class ElectionSerializer(serializers.ModelSerializer):
    candidates = CandidateSerializer(many=True, read_only=True)

    class Meta:
        model = Election
        fields = [
            "id",
            "election_committee_members",
            "election_date",
            "status",
            "candidates",
            "created_at",
            "updated_at",
        ]


class SubCommitteeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCommittee
        fields = ["id", "name", "tor_description", "created_at", "updated_at"]


class OathRecordSerializer(serializers.ModelSerializer):
    committee_member_name = serializers.SerializerMethodField()

    class Meta:
        model = OathRecord
        fields = ["id", "committee_member", "committee_member_name", "oath_date"]

    def get_committee_member_name(self, obj):
        return obj.committee_member.get_member_name()


class NoConfidenceMotionSerializer(serializers.ModelSerializer):
    target_member_name = serializers.SerializerMethodField()

    class Meta:
        model = NoConfidenceMotion
        fields = [
            "id",
            "target_type",
            "target_committee_member",
            "target_member_name",
            "signatures_count",
            "filed_date",
            "assembly_decision",
            "created_at",
            "updated_at",
        ]

    def get_target_member_name(self, obj):
        if obj.target_committee_member:
            return obj.target_committee_member.get_member_name()
        return None


class HandoverRecordSerializer(serializers.ModelSerializer):
    outgoing_name = serializers.SerializerMethodField()
    incoming_name = serializers.SerializerMethodField()

    class Meta:
        model = HandoverRecord
        fields = [
            "id",
            "outgoing_committee_member",
            "outgoing_name",
            "incoming_committee_member",
            "incoming_name",
            "cash_amount",
            "assets_summary",
            "deadline_date",
            "completed_date",
            "status",
            "created_at",
            "updated_at",
        ]

    def get_outgoing_name(self, obj):
        return obj.outgoing_committee_member.get_member_name()

    def get_incoming_name(self, obj):
        if obj.incoming_committee_member:
            return obj.incoming_committee_member.get_member_name()
        return None
