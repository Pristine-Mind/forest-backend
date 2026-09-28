from django.contrib.auth import authenticate
from rest_framework import serializers

from apps.core.models import SystemConfig, User
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError as DjangoValidationError


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = authenticate(
                request=self.context.get("request"),
                username=email,
                password=password,
            )
            if not user:
                raise serializers.ValidationError(
                    "Unable to log in with provided credentials.",
                    code="authorization",
                )
            if not user.is_active:
                raise serializers.ValidationError(
                    "User account is disabled.",
                    code="authorization",
                )
        else:
            raise serializers.ValidationError(
                'Must include "email" and "password".',
                code="authorization",
            )

        attrs["user"] = user
        return attrs


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


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs):
        user = self.context["request"].user

        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        if attrs["new_password"] == attrs["old_password"]:
            raise serializers.ValidationError(
                {"new_password": "New password must be different from the current one."}
            )

        # Runs the validators from AUTH_PASSWORD_VALIDATORS in settings.py
        try:
            password_validation.validate_password(attrs["new_password"], user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})

        return attrs