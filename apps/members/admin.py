from django.contrib import admin

from apps.members.models import Household, Member, MembershipRenewal


class MemberInline(admin.TabularInline):
    model = Member
    extra = 0
    fields = ["full_name", "citizenship_no", "membership_type", "membership_status"]


class MembershipRenewalInline(admin.TabularInline):
    model = MembershipRenewal
    extra = 0
    fields = ["fiscal_year", "fee_tier", "fee_charged", "paid_date"]


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = [
        "household_head_name",
        "tole",
        "wealth_class",
        "population_male",
        "population_female",
        "registration_date",
        "status",
    ]
    list_filter = ["wealth_class", "status", "education_level"]
    search_fields = ["household_head_name", "tole"]
    inlines = [MemberInline]


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = [
        "full_name",
        "citizenship_no",
        "household",
        "membership_type",
        "membership_status",
        "date_joined",
    ]
    list_filter = ["membership_type", "membership_status"]
    search_fields = ["full_name", "citizenship_no", "household__household_head_name"]
    inlines = [MembershipRenewalInline]
    autocomplete_fields = ["household", "user"]


@admin.register(MembershipRenewal)
class MembershipRenewalAdmin(admin.ModelAdmin):
    list_display = ["member", "fiscal_year", "fee_tier", "fee_charged", "paid_date"]
    list_filter = ["fee_tier", "fiscal_year"]
    search_fields = ["member__full_name", "member__citizenship_no"]
    autocomplete_fields = ["member"]
