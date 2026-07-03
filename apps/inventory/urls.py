from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.inventory.views import (
    PriceRateViewSet,
    SaleViewSet,
    StockLedgerViewSet,
    StockTransactionViewSet,
)

router = DefaultRouter()
router.register(r"ledgers", StockLedgerViewSet)
router.register(r"stock-transactions", StockTransactionViewSet)
router.register(r"price-rates", PriceRateViewSet)
router.register(r"sales", SaleViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
