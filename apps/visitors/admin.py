from django.contrib import admin

from apps.visitors.models import OfficialGuestLog, VisitorEntry, VisitorFeeRate


@admin.register(VisitorFeeRate)
class VisitorFeeRateAdmin(admin.ModelAdmin):
    list_display = ["visit_purpose", "fee_per_visitor_per_day"]


@admin.register(VisitorEntry)
class VisitorEntryAdmin(admin.ModelAdmin):
    list_display = [
        "entry_date",
        "visit_purpose",
        "visitor_count",
        "days",
        "fee_waived",
        "total_amount",
        "receipt_no",
    ]
    list_filter = ["visit_purpose", "fee_waived"]


@admin.register(OfficialGuestLog)
class OfficialGuestLogAdmin(admin.ModelAdmin):
    list_display = ["visitor_name", "designation", "visit_start_date", "visit_end_date"]
    search_fields = ["visitor_name", "designation"]
