from rest_framework import serializers

from apps.core.models import SystemConfig
from apps.fund.models import (
    Audit,
    BankAccount,
    BankTransaction,
    CashTransaction,
    FundAllocationRule,
    PublicAudit,
    BudgetAllocation,
)


class FundAllocationRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundAllocationRule
        fields = [
            "id",
            "forest_dev_min_percent",
            "poor_targeted_min_percent",
            "effective_from",
            "created_at",
            "updated_at",
        ]


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = [
            "id",
            "bank_name",
            "account_number",
            "signatories",
            "min_signatures_required",
            "created_at",
            "updated_at",
        ]


class CashTransactionSerializer(serializers.ModelSerializer):
    requires_committee_approval = serializers.BooleanField(read_only=True)

    class Meta:
        model = CashTransaction
        fields = [
            "id",
            "type",
            "source_or_purpose",
            "amount",
            "requires_committee_approval",
            "approved_by",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        amount = attrs.get("amount")
        approved_by = attrs.get("approved_by")
        config = SystemConfig.get()
        if (
            amount
            and amount > min(config.cash_chair_approval_limit, config.cash_treasurer_approval_limit)
            and not approved_by
        ):
            raise serializers.ValidationError(
                {"approved_by": "Transactions above the configured limit require committee approval."}
            )
        return attrs


class AuditSerializer(serializers.ModelSerializer):
    audit_tier = serializers.CharField(read_only=True)

    class Meta:
        model = Audit
        fields = [
            "id",
            "fiscal_year",
            "total_income",
            "audit_tier",
            "auditor_name",
            "findings",
            "irregularities_recovered",
            "created_at",
            "updated_at",
        ]


class PublicAuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicAudit
        fields = [
            "id",
            "fiscal_year",
            "presentation_date",
            "assembly_approval",
            "created_at",
            "updated_at",
        ]


class BankTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankTransaction
        fields = [
            "id",
            "account",
            "transaction_type",
            "amount",
            "transaction_date",
            "description",
            "created_at",
            "updated_at",
        ]


class BudgetAllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetAllocation
        fields = [
            "id",
            "fiscal_year",
            "title",
            "work_description",
            "allocated_amount",
            "approved_date",
            "work_status",
            "remarks",
            "approved_by",
            "created_at",
            "updated_at",
        ]
