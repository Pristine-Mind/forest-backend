from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.livelihood.views import (
    LivelihoodProgramRecordViewSet,
    PovertyGroupAgreementViewSet,
    RevolvingFundLoanViewSet,
)

router = DefaultRouter()
router.register(r"revolving-loans", RevolvingFundLoanViewSet)
router.register(r"program-records", LivelihoodProgramRecordViewSet)
router.register(r"poverty-group-agreements", PovertyGroupAgreementViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
