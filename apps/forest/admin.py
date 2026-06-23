from django.contrib import admin

from apps.forest.models import (
    ForestBlock,
    OperationalPlan,
    Species,
    TreeCountHistory,
    TreeCountRegister,
)


class TreeCountHistoryInline(admin.TabularInline):
    model = TreeCountHistory
    extra = 0
    readonly_fields = ["change_amount", "reference_harvest", "change_date", "note"]


@admin.register(ForestBlock)
class ForestBlockAdmin(admin.ModelAdmin):
    list_display = ["block_name", "area_hectares"]
    search_fields = ["block_name"]


@admin.register(Species)
class SpeciesAdmin(admin.ModelAdmin):
    search_fields = ["species_name"]


@admin.register(OperationalPlan)
class OperationalPlanAdmin(admin.ModelAdmin):
    list_display = ["valid_from", "valid_to", "approved_harvest_limit"]


@admin.register(TreeCountRegister)
class TreeCountRegisterAdmin(admin.ModelAdmin):
    list_display = ["species", "block", "total_count", "harvested_count", "remaining_count", "last_updated"]
    list_filter = ["species", "block"]
    readonly_fields = ["harvested_count", "remaining_count", "last_updated"]
    inlines = [TreeCountHistoryInline]
    autocomplete_fields = ["species", "block"]


@admin.register(TreeCountHistory)
class TreeCountHistoryAdmin(admin.ModelAdmin):
    list_display = ["record", "change_amount", "change_date", "reference_harvest"]
    list_filter = ["change_date"]
