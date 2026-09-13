from rest_framework import serializers

from apps.core.models import SystemConfig, Notification
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
    submitted_by_name = serializers.CharField(source='submitted_by.full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.full_name', read_only=True)

    class Meta:
        model = CashTransaction
        fields = [
            "id",
            "type",
            "source_or_purpose",
            "amount",
            "payment_type",
            "cheque_number",
            "cheque_bank_name",
            "requires_committee_approval",
            "approval_status",
            "submitted_for_approval_at",
            "submitted_by",
            "submitted_by_name",
            "approved_by",
            "approved_by_name",
            "approved_at",
            "rejection_reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "requires_committee_approval",
            "approval_status",
            "submitted_for_approval_at",
            "submitted_by",
            "submitted_by_name",
            "approved_by",
            "approved_by_name",
            "approved_at",
            "rejection_reason",
        ]

    def validate(self, attrs):
        # amount = attrs.get("amount")
        # approval_status = attrs.get("approval_status")
        # config = SystemConfig.get()
        # if (
        #     amount
        #     and amount > min(config.cash_chair_approval_limit, config.cash_treasurer_approval_limit)
        #     and not approval_status == CashTransaction.ApprovalStatus.APPROVED
        # ):
        #     raise serializers.ValidationError(
        #         {"amount": "Large amounts require committee approval. Use the 'submit for approval' action."}
        #     )
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
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)

    class Meta:
        model = BankTransaction
        fields = [
            "id",
            "account",
            "transaction_type",
            "amount",
            "transaction_date",
            "description",
            "created_by",
            "created_by_name",
            "requires_committee_approval",
            "approved_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_by", "created_by_name", "requires_committee_approval"]


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


class NotificationSerializer(serializers.ModelSerializer):
    recipient_name = serializers.CharField(source='recipient.full_name', read_only=True)
    actioned_by_name = serializers.CharField(source='actioned_by.full_name', read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "recipient",
            "recipient_name",
            "notification_type",
            "title",
            "description",
            "status",
            "content_type",
            "object_id",
            "action_required",
            "action_deadline",
            "read_at",
            "actioned_at",
            "actioned_by",
            "actioned_by_name",
            "action_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "recipient",
            "recipient_name",
            "read_at",
            "actioned_at",
            "actioned_by",
            "actioned_by_name",
        ]
