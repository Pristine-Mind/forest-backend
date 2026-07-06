from django.contrib import admin
from django.utils.html import format_html

from .models import (
    CuttingRegister,
    CuttingRegisterItem,
    FellingRegister,
    FellingRegisterEntry,
    TreeSurveyForm,
    TreeSurveyFormItem,
)


class TreeSurveyFormItemInline(admin.TabularInline):
    """Inline admin for tree survey form items"""

    model = TreeSurveyFormItem
    extra = 1
    fields = [
        "serial_number",
        "species",
        "girth_cm",
        "height_m",
        "volume_cubic_m",
        "fuelwood_volume_cubic_m",
        "wood_type",
    ]


@admin.register(TreeSurveyForm)
class TreeSurveyFormAdmin(admin.ModelAdmin):
    """Admin interface for tree survey forms"""

    list_display = [
        "form_number",
        "survey_date",
        "block",
        "district",
        "municipality",
        "tree_count_display",
        "total_volume_display",
        "pdf_download_link",
    ]
    list_filter = ["survey_date", "block", "district", "municipality"]
    search_fields = ["form_number", "district", "municipality"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "survey_date"
    inlines = [TreeSurveyFormItemInline]

    fieldsets = (
        ("Form Information", {"fields": ("form_number", "survey_date")}),
        (
            "Location Information",
            {
                "fields": (
                    "block",
                    "operational_plan",
                    "district",
                    "municipality",
                    "ward_number",
                    "plot_number",
                    "forest_category",
                )
            },
        ),
        (
            "Approvals",
            {
                "fields": (
                    "community_representative",
                    "community_representative_sign_date",
                    "forest_officer",
                    "forest_officer_sign_date",
                )
            },
        ),
        ("Additional Information", {"fields": ("notes",), "classes": ("collapse",)}),
        ("Metadata", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def tree_count_display(self, obj):
        """Display tree count in admin list"""
        count = obj.tree_items.count()
        return f"{count} trees"

    tree_count_display.short_description = "Trees"

    def total_volume_display(self, obj):
        """Display total volume in admin list"""
        total = obj.get_total_volume()
        return f"{total:.2f} m³"

    total_volume_display.short_description = "Total Volume"

    def pdf_download_link(self, obj):
        """Provide download link for PDF"""
        if obj.pk:
            url = f"/api/v1/survey-forms/{obj.pk}/pdf/"
            return format_html('<a class="button" href="{}">Download PDF</a>', url)
        return "-"

    pdf_download_link.short_description = "Export"


@admin.register(TreeSurveyFormItem)
class TreeSurveyFormItemAdmin(admin.ModelAdmin):
    """Admin interface for tree survey form items"""

    list_display = [
        "survey_form",
        "serial_number",
        "species",
        "girth_cm",
        "height_m",
        "volume_cubic_m",
        "wood_type",
    ]
    list_filter = ["survey_form", "wood_type", "species"]
    search_fields = ["survey_form__form_number", "species__species_name"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Form Reference", {"fields": ("survey_form", "serial_number")}),
        ("Tree Information", {"fields": ("species", "wood_type")}),
        ("Measurements", {"fields": ("girth_cm", "height_m")}),
        ("Volume Calculations", {"fields": ("volume_cubic_m", "fuelwood_volume_cubic_m")}),
        ("Additional Information", {"fields": ("remarks",), "classes": ("collapse",)}),
        ("Metadata", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


class CuttingRegisterItemInline(admin.TabularInline):
    """Inline admin for cutting register items"""

    model = CuttingRegisterItem
    extra = 1
    fields = [
        "serial_number",
        "entry_time",
        "plot_number",
        "quota_number",
        "species",
        "size_measurement",
        "volume_cubic_m",
    ]


@admin.register(CuttingRegister)
class CuttingRegisterAdmin(admin.ModelAdmin):
    """Admin interface for cutting registers"""

    list_display = [
        "form_number",
        "register_date",
        "block",
        "district",
        "cutting_location",
        "item_count_display",
        "total_volume_display",
        "pdf_download_link",
    ]
    list_filter = ["register_date", "block", "district", "zone"]
    search_fields = ["form_number", "district", "municipality", "cutting_location"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "register_date"
    inlines = [CuttingRegisterItemInline]

    fieldsets = (
        ("Form Information", {"fields": ("form_number", "register_date")}),
        (
            "Location Information",
            {
                "fields": (
                    "block",
                    "operational_plan",
                    "zone",
                    "district",
                    "municipality",
                    "ward_number",
                )
            },
        ),
        (
            "Forest Information",
            {
                "fields": (
                    "forest_classification",
                    "block_plot_name",
                    "block_plot_type",
                    "cutting_location",
                )
            },
        ),
        (
            "Community Representative",
            {
                "fields": (
                    "community_representative_name",
                    "community_representative_position",
                    "community_representative_sign_date",
                )
            },
        ),
        (
            "Forest Officer",
            {
                "fields": (
                    "forest_officer_name",
                    "forest_officer_position",
                    "forest_officer_sign_date",
                )
            },
        ),
        ("Additional Information", {"fields": ("notes",), "classes": ("collapse",)}),
        ("Metadata", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def item_count_display(self, obj):
        """Display item count in admin list"""
        count = obj.get_item_count()
        return f"{count} items"

    item_count_display.short_description = "Items"

    def total_volume_display(self, obj):
        """Display total volume in admin list"""
        total = obj.get_total_volume()
        return f"{total:.2f} m³"

    total_volume_display.short_description = "Total Volume"

    def pdf_download_link(self, obj):
        """Provide download link for PDF"""
        if obj.pk:
            url = f"/api/v1/cutting-registers/{obj.pk}/pdf/"
            return format_html('<a class="button" href="{}">Download PDF</a>', url)
        return "-"

    pdf_download_link.short_description = "Export"


@admin.register(CuttingRegisterItem)
class CuttingRegisterItemAdmin(admin.ModelAdmin):
    """Admin interface for cutting register items"""

    list_display = [
        "cutting_register",
        "serial_number",
        "entry_time",
        "plot_number",
        "species",
        "volume_cubic_m",
    ]
    list_filter = ["cutting_register", "species", "entry_time"]
    search_fields = ["cutting_register__form_number", "species__species_name", "plot_number"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Register Reference", {"fields": ("cutting_register", "serial_number")}),
        ("Entry Time", {"fields": ("entry_time",)}),
        (
            "Plot & Quota Information",
            {"fields": ("plot_number", "quota_number")},
        ),
        ("Species Information", {"fields": ("species", "size_measurement")}),
        ("Volume", {"fields": ("volume_cubic_m",)}),
        (
            "Additional Information",
            {"fields": ("comments", "remarks"), "classes": ("collapse",)},
        ),
        ("Metadata", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


class FellingRegisterEntryInline(admin.TabularInline):
    model = FellingRegisterEntry
    extra = 1
    fields = (
        "entry_date",
        "entry_time",
        "rawana_number",
        "golia_number",
        "species",
        "measurement_size",
        "volume_cubic_feet",
        "firewood_chatta",
        "remarks",
    )


@admin.register(FellingRegister)
class FellingRegisterAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "felling_location",
        "district",
        "cutting_agency_name",
        "tree_count",
        "created_at",
    )
    search_fields = ("felling_location", "district", "cutting_agency_name")
    list_filter = ("district",)
    inlines = [FellingRegisterEntryInline]
