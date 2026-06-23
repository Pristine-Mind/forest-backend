from rest_framework import serializers

from apps.livelihood.models import (
    LivelihoodProgramRecord,
    PovertyGroupAgreement,
    RevolvingFundLoan,
)


class RevolvingFundLoanSerializer(serializers.ModelSerializer):
    household_name = serializers.CharField(source="household.household_head_name", read_only=True)

    class Meta:
        model = RevolvingFundLoan
        fields = [
            "id",
            "household",
            "household_name",
            "amount",
            "issue_date",
            "repaid_amount",
            "status",
            "created_at",
            "updated_at",
        ]


class LivelihoodProgramRecordSerializer(serializers.ModelSerializer):
    household_name = serializers.CharField(source="household.household_head_name", read_only=True)

    class Meta:
        model = LivelihoodProgramRecord
        fields = [
            "id",
            "household",
            "household_name",
            "program_type",
            "amount_or_value",
            "program_date",
            "description",
            "created_at",
            "updated_at",
        ]


class PovertyGroupAgreementSerializer(serializers.ModelSerializer):
    class Meta:
        model = PovertyGroupAgreement
        fields = [
            "id",
            "subgroup_name",
            "member_households",
            "forest_land_area",
            "term_start",
            "term_end",
            "revenue_share_percent",
            "status",
            "created_at",
            "updated_at",
        ]
