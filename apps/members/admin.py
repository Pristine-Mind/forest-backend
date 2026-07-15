from django.contrib import admin

from apps.members.models import Household, Member, MembershipRenewal


class MemberInline(admin.TabularInline):
    model = Member
    extra = 0
    fields = ["full_name", "relation", "member_photo"]


class MembershipRenewalInline(admin.TabularInline):
    model = MembershipRenewal
    extra = 0
    fields = ["fiscal_year", "fee_tier", "fee_charged", "paid_date"]


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = [
        "household_head_name",
        "english_name",
        "tole",
        "citizenship_no",
        "wealth_class",
        "membership_type",
        "membership_status",
        "date_joined",
        "registration_date",
        "status",
    ]
    list_filter = ["wealth_class", "status", "education_level"]
    search_fields = ["household_head_name", "tole", "citizenship_no"]
    inlines = [MemberInline]


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = [
        "full_name",
        "household",
    ]
    list_filter = []
    search_fields = ["full_name", "household__citizenship_no"]
    inlines = [MembershipRenewalInline]
    autocomplete_fields = ["household", "user"]


@admin.register(MembershipRenewal)
class MembershipRenewalAdmin(admin.ModelAdmin):
    list_display = ["member", "fiscal_year", "fee_tier", "fee_charged", "paid_date"]
    list_filter = ["fee_tier", "fiscal_year"]
    search_fields = ["member__full_name", "member__citizenship_no"]
    autocomplete_fields = ["member"]
