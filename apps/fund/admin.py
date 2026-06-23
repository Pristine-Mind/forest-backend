from django.contrib import admin

from apps.fund.models import (
    Audit,
    BankAccount,
    CashTransaction,
    FundAllocationRule,
    PublicAudit,
)


@admin.register(FundAllocationRule)
class FundAllocationRuleAdmin(admin.ModelAdmin):
    list_display = ["forest_dev_min_percent", "poor_targeted_min_percent", "effective_from"]


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ["bank_name", "account_number", "min_signatures_required"]


@admin.register(CashTransaction)
class CashTransactionAdmin(admin.ModelAdmin):
    list_display = ["type", "source_or_purpose", "amount", "requires_committee_approval", "approved_by"]
    list_filter = ["type", "requires_committee_approval"]


@admin.register(Audit)
class AuditAdmin(admin.ModelAdmin):
    list_display = ["fiscal_year", "total_income", "audit_tier", "auditor_name"]
    list_filter = ["audit_tier"]


@admin.register(PublicAudit)
class PublicAuditAdmin(admin.ModelAdmin):
    list_display = ["fiscal_year", "presentation_date", "assembly_approval"]
