from rest_framework import serializers

from apps.members.models import Household, Member, MembershipRenewal


class HouseholdSerializer(serializers.ModelSerializer):
    entry_fee_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Household
        fields = [
            "id",
            "household_head_name",
            "tole",
            "wealth_class",
            "population_male",
            "population_female",
            "livestock_cattle",
            "livestock_buffalo",
            "livestock_goat",
            "education_level",
            "occupation",
            "caste_ethnicity",
            "registration_date",
            "entry_fee_type",
            "entry_fee_due",
            "status",
            "created_at",
            "updated_at",
        ]


class MemberSerializer(serializers.ModelSerializer):
    household_name = serializers.CharField(source="household.household_head_name", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Member
        fields = [
            "id",
            "household",
            "household_name",
            "user",
            "user_email",
            "full_name",
            "citizenship_no",
            "membership_type",
            "membership_status",
            "date_joined",
            "created_at",
            "updated_at",
        ]


class MemberListSerializer(MemberSerializer):
    """Light serializer for list views."""

    class Meta(MemberSerializer.Meta):
        fields = [
            "id",
            "full_name",
            "citizenship_no",
            "membership_status",
            "household_name",
        ]


class MembershipRenewalSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.full_name", read_only=True)

    class Meta:
        model = MembershipRenewal
        fields = [
            "id",
            "member",
            "member_name",
            "fiscal_year",
            "fee_tier",
            "fee_charged",
            "paid_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["fee_tier", "fee_charged"]
