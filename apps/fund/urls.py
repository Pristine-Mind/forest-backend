from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.fund.views import (
    AuditViewSet,
    BankAccountViewSet,
    CashTransactionViewSet,
    FundAllocationRuleViewSet,
    PublicAuditViewSet,
)

router = DefaultRouter()
router.register(r"allocation-rules", FundAllocationRuleViewSet)
router.register(r"bank-accounts", BankAccountViewSet)
router.register(r"cash-transactions", CashTransactionViewSet)
router.register(r"audits", AuditViewSet)
router.register(r"public-audits", PublicAuditViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
