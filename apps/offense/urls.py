from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.offense.views import (
    EvidenceItemViewSet,
    HearingRecordViewSet,
    InformantRewardViewSet,
    OffenseReportViewSet,
    PatrolLogViewSet,
)

router = DefaultRouter()
router.register(r"reports", OffenseReportViewSet)
router.register(r"evidence", EvidenceItemViewSet)
router.register(r"hearings", HearingRecordViewSet)
router.register(r"informant-rewards", InformantRewardViewSet)
router.register(r"patrol-logs", PatrolLogViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
