from rest_framework import serializers

from apps.governance.models import (
    Candidate,
    CommitteeMember,
    Election,
    HandoverRecord,
    NoConfidenceMotion,
    OathRecord,
    SubCommittee,
)


class CommitteeMemberSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.full_name", read_only=True)
    subcommittee_names = serializers.SerializerMethodField()

    class Meta:
        model = CommitteeMember
        fields = [
            "id",
            "member",
            "member_name",
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
        ]

    def get_subcommittee_names(self, obj):
        return [sc.get_name_display() for sc in obj.subcommittees.all()]


class CandidateSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.full_name", read_only=True)

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
    committee_member_name = serializers.CharField(source="committee_member.member.full_name", read_only=True)

    class Meta:
        model = OathRecord
        fields = ["id", "committee_member", "committee_member_name", "oath_date"]


class NoConfidenceMotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoConfidenceMotion
        fields = [
            "id",
            "target_type",
            "target_committee_member",
            "signatures_count",
            "filed_date",
            "assembly_decision",
            "created_at",
            "updated_at",
        ]


class HandoverRecordSerializer(serializers.ModelSerializer):
    outgoing_name = serializers.CharField(source="outgoing_committee_member.member.full_name", read_only=True)
    incoming_name = serializers.CharField(
        source="incoming_committee_member.member.full_name", read_only=True, allow_null=True
    )

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
