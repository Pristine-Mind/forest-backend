from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.fund.views import (
    AuditViewSet,
    BankAccountViewSet,
    BankTransactionViewSet,
    CashTransactionViewSet,
    FundAllocationRuleViewSet,
    PublicAuditViewSet,
    BudgetAllocationViewSet,
)

router = DefaultRouter()
router.register(r"allocation-rules", FundAllocationRuleViewSet)
router.register(r"bank-accounts", BankAccountViewSet)
router.register(r"bank-transactions", BankTransactionViewSet)
router.register(r"cash-transactions", CashTransactionViewSet)
router.register(r"audits", AuditViewSet)
router.register(r"public-audits", PublicAuditViewSet)
router.register(r"budget-allocations", BudgetAllocationViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
