from django.contrib import admin

from apps.livelihood.models import (
    LivelihoodProgramRecord,
    PovertyGroupAgreement,
    RevolvingFundLoan,
)


@admin.register(RevolvingFundLoan)
class RevolvingFundLoanAdmin(admin.ModelAdmin):
    list_display = ["household", "amount", "issue_date", "repaid_amount", "status"]
    list_filter = ["status"]
    autocomplete_fields = ["household"]


@admin.register(LivelihoodProgramRecord)
class LivelihoodProgramRecordAdmin(admin.ModelAdmin):
    list_display = ["household", "program_type", "amount_or_value", "program_date"]
    list_filter = ["program_type"]
    autocomplete_fields = ["household"]


@admin.register(PovertyGroupAgreement)
class PovertyGroupAgreementAdmin(admin.ModelAdmin):
    list_display = ["subgroup_name", "forest_land_area", "term_start", "term_end", "status"]
    list_filter = ["status"]
