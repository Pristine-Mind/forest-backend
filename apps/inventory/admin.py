from django.contrib import admin

from apps.inventory.models import PriceRate, Sale, StockLedger, StockTransaction


class StockTransactionInline(admin.TabularInline):
    model = StockTransaction
    extra = 0
    readonly_fields = ["transaction_type", "quantity", "reference_type", "reference_id"]


@admin.register(StockLedger)
class StockLedgerAdmin(admin.ModelAdmin):
    list_display = ["species", "grade", "quantity_available"]
    list_filter = ["species", "grade"]
    inlines = [StockTransactionInline]
    autocomplete_fields = ["species"]


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ["stock", "transaction_type", "quantity", "reference_type", "reference_id"]
    list_filter = ["transaction_type", "reference_type"]


@admin.register(PriceRate)
class PriceRateAdmin(admin.ModelAdmin):
    list_display = ["species", "grade", "buyer_type", "rate_per_unit", "effective_from"]
    list_filter = ["buyer_type", "grade"]
    autocomplete_fields = ["species"]


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = [
        "buyer_name",
        "buyer_type",
        "species",
        "grade",
        "quantity",
        "rate_applied",
        "total_amount",
        "payment_status",
        "receipt_no",
    ]
    list_filter = ["buyer_type", "payment_status", "grade"]
    search_fields = ["buyer_name", "member__full_name"]
    autocomplete_fields = ["species", "member"]
