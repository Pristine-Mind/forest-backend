from django.contrib import admin

from apps.forest.models import (
    ForestBlock,
    HarvestLog,
    OperationalPlan,
    PoleCountRegister,
    Species,
    TimberCollection,
    TreeCountHistory,
    TreeCountRegister,
    WildlifeSpecies,
)


class TreeCountHistoryInline(admin.TabularInline):
    model = TreeCountHistory
    extra = 0
    readonly_fields = ["change_amount", "reference_harvest", "change_date", "note"]
    fields = ["change_amount", "reference_harvest", "change_date", "note"]


class HarvestLogInline(admin.TabularInline):
    model = HarvestLog
    extra = 0
    readonly_fields = ["harvest_date", "harvest_quantity_cubic_m", "notes"]
    fields = ["harvest_date", "harvest_quantity_cubic_m", "reference_harvest_request", "notes"]


@admin.register(ForestBlock)
class ForestBlockAdmin(admin.ModelAdmin):
    list_display = ["block_no", "block_name", "total_area_ha", "forest_type", "forest_condition", "created_at"]
    search_fields = ["block_no", "block_name", "title"]
    list_filter = ["forest_type", "forest_condition", "created_at"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Basic Information", {"fields": ("block_no", "block_name", "title")}),
        ("Area Details", {"fields": ("total_area_ha", "productive_area_ha", "canopy_percent")}),
        ("Forest Information", {"fields": ("forest_type", "forest_condition", "soil_types")}),
        ("Species & Products", {"fields": ("major_species", "non_timber_forest_products", "wildlife_species")}),
        ("Management", {"fields": ("forest_management_activities", "boundaries")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(Species)
class SpeciesAdmin(admin.ModelAdmin):
    list_display = ["species_name", "scientific_name", "local_name"]
    search_fields = ["species_name", "scientific_name", "local_name"]


@admin.register(WildlifeSpecies)
class WildlifeSpeciesAdmin(admin.ModelAdmin):
    list_display = ["species_name", "scientific_name", "local_name"]
    search_fields = ["species_name", "scientific_name", "local_name"]


@admin.register(OperationalPlan)
class OperationalPlanAdmin(admin.ModelAdmin):
    list_display = ["valid_from", "valid_to", "approved_harvest_limit", "created_at"]
    list_filter = ["valid_from", "valid_to"]
    search_fields = ["description"]


@admin.register(TreeCountRegister)
class TreeCountRegisterAdmin(admin.ModelAdmin):
    list_display = [
        "tree_number",
        "species",
        "block",
        "plot_number",
        "girth_cm",
        "height_m",
        "tree_class",
        "total_volume_cubic_m",
        "is_harvestable",
        "is_active",
    ]
    list_filter = [
        "block",
        "species",
        "tree_class",
        "is_harvestable",
        "is_active",
        "survey_date",
    ]
    search_fields = [
        "block__block_name",
        "species__species_name",
        "notes",
    ]
    readonly_fields = [
        "basal_area_sqm",
        "stem_volume_cubic_m",
        "r_factor",
        "branch_volume_cubic_m",
        "total_volume_cubic_m",
        "r_less_than_10",
        "volume_less_than_10_cubic_m",
        "gross_volume_cubic_m",
        "net_volume_cubic_m",
        "fuelwood_volume_cubic_m",
        "created_at",
        "updated_at",
    ]
    fieldsets = (
        ("Plot Information", {"fields": ("block", "plot_number", "tree_number")}),
        ("Species Information", {"fields": ("species", "operational_plan")}),
        ("Tree Measurements", {"fields": ("girth_cm", "height_m", "tree_class", "survey_date")}),
        (
            "Calculated Volumes",
            {
                "fields": (
                    "basal_area_sqm",
                    "stem_volume_cubic_m",
                    "r_factor",
                    "branch_volume_cubic_m",
                    "total_volume_cubic_m",
                    "r_less_than_10",
                    "volume_less_than_10_cubic_m",
                    "gross_volume_cubic_m",
                    "net_volume_cubic_m",
                    "fuelwood_volume_cubic_m",
                )
            },
        ),
        ("Status & Metadata", {"fields": ("is_harvestable", "is_active", "notes", "created_at", "updated_at")}),
    )
    inlines = [TreeCountHistoryInline, HarvestLogInline]
    autocomplete_fields = ["block", "species", "operational_plan"]
    list_per_page = 50


@admin.register(TreeCountHistory)
class TreeCountHistoryAdmin(admin.ModelAdmin):
    list_display = ["record", "change_amount", "change_date", "reference_harvest"]
    list_filter = ["change_date", "record__block", "record__species"]
    search_fields = ["record__species__species_name", "note"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(HarvestLog)
class HarvestLogAdmin(admin.ModelAdmin):
    list_display = ["tree_record", "harvest_date", "harvest_quantity_cubic_m", "reference_harvest_request"]
    list_filter = ["harvest_date", "tree_record__block", "tree_record__species"]
    search_fields = ["tree_record__species__species_name", "notes"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(TimberCollection)
class TimberCollectionAdmin(admin.ModelAdmin):
    list_display = ["block", "species", "wood_volume", "firewood", "created_at"]
    list_filter = ["block", "species"]
    search_fields = ["block__block_name", "species__species_name"]
    autocomplete_fields = ["block", "species"]
    ordering = ["block", "species"]

    fieldsets = (
        ("Location", {"fields": ("block", "species")}),
        ("Quantities", {"fields": ("wood_volume", "firewood")}),
        ("Metadata", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(PoleCountRegister)
class PoleCountRegisterAdmin(admin.ModelAdmin):
    list_display = [
        "tree_number",
        "species",
        "block",
        "plot_number",
        "girth_cm",
        "height_m",
        "tree_class",
        "total_volume_cubic_m",
        "is_harvestable",
        "is_active",
    ]
    list_filter = [
        "block",
        "species",
        "tree_class",
        "is_harvestable",
        "is_active",
        "survey_date",
    ]
    search_fields = [
        "block__block_name",
        "species__species_name",
        "notes",
    ]
    readonly_fields = [
        "basal_area_sqm",
        "stem_volume_cubic_m",
        "r_factor",
        "branch_volume_cubic_m",
        "total_volume_cubic_m",
        "r_less_than_10",
        "volume_less_than_10_cubic_m",
        "gross_volume_cubic_m",
        "net_volume_cubic_m",
        "fuelwood_volume_cubic_m",
        "created_at",
        "updated_at",
    ]
    fieldsets = (
        ("Plot Information", {"fields": ("block", "plot_number", "tree_number")}),
        ("Species Information", {"fields": ("species", "operational_plan")}),
        ("Tree Measurements", {"fields": ("girth_cm", "height_m", "tree_class", "survey_date")}),
        (
            "Calculated Volumes",
            {
                "fields": (
                    "basal_area_sqm",
                    "stem_volume_cubic_m",
                    "r_factor",
                    "branch_volume_cubic_m",
                    "total_volume_cubic_m",
                    "r_less_than_10",
                    "volume_less_than_10_cubic_m",
                    "gross_volume_cubic_m",
                    "net_volume_cubic_m",
                    "fuelwood_volume_cubic_m",
                )
            },
        ),
        ("Status & Metadata", {"fields": ("is_harvestable", "is_active", "notes", "created_at", "updated_at")}),
    )
    # inlines = [TreeCountHistoryInline, HarvestLogInline]
    autocomplete_fields = ["block", "species", "operational_plan"]
    list_per_page = 50
