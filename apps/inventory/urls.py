from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.inventory.views import (
    PriceRateViewSet,
    SaleViewSet,
    StockLedgerViewSet,
    StockTransactionViewSet,
    TimberLogEntryViewSet,
)

router = DefaultRouter()
router.register(r"ledgers", StockLedgerViewSet)
router.register(r"stock-transactions", StockTransactionViewSet)
router.register(r"price-rates", PriceRateViewSet)
router.register(r"sales", SaleViewSet)
router.register(r"timber-log-entries", TimberLogEntryViewSet, basename="timberlogentry")

urlpatterns = [
    path("", include(router.urls)),
]
