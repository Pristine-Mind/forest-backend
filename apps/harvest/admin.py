from django.contrib import admin

from apps.harvest.models import HarvestRequest


@admin.register(HarvestRequest)
class HarvestRequestAdmin(admin.ModelAdmin):
    list_display = [
        "source_type",
        "member",
        "operation_name",
        "species",
        "quantity",
        "status",
        "requested_date",
        "approved_by",
    ]
    list_filter = ["status", "source_type", "requested_date"]
    search_fields = ["member__full_name", "species__species_name", "operation_name"]
    autocomplete_fields = ["member", "species", "approved_by"]
