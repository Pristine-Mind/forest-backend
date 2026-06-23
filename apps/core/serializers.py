from rest_framework import serializers

from apps.core.models import SystemConfig, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["date_joined"]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "password",
            "is_active",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class SystemConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemConfig
        fields = [
            "id",
            "new_household_entry_fee",
            "split_household_entry_fee",
            "renewal_fee_on_time",
            "renewal_fee_overdue_3yr",
            "renewal_fee_overdue_5yr",
            "renewal_fee_overdue_5yr_plus",
            "membership_cancellation_years",
            "current_fiscal_year",
            "forest_dev_min_percent",
            "poor_targeted_min_percent",
            "cash_chair_approval_limit",
            "cash_treasurer_approval_limit",
            "audit_external_threshold",
            "informant_reward_percent",
            "no_confidence_signature_percent",
            "handover_deadline_days",
            "min_female_committee_members",
            "min_dalit_or_minority_committee_members",
        ]
