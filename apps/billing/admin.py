from django.contrib import admin

from apps.billing.models import FeeCollection, Receipt


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ["receipt_no", "reference_type", "reference_id", "amount", "issued_date", "issued_by"]
    list_filter = ["reference_type", "issued_date"]
    search_fields = ["receipt_no"]


@admin.register(FeeCollection)
class FeeCollectionAdmin(admin.ModelAdmin):
    list_display = ["member", "fee_type", "amount", "amount_paid", "payment_status", "receipt_no"]
    list_filter = ["fee_type", "payment_status"]
    search_fields = ["member__full_name", "member__citizenship_no"]
    autocomplete_fields = ["member"]
