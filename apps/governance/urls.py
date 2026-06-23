from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.governance.views import (
    CandidateViewSet,
    CommitteeMemberViewSet,
    ElectionViewSet,
    HandoverRecordViewSet,
    NoConfidenceMotionViewSet,
    OathRecordViewSet,
    SubCommitteeViewSet,
)

router = DefaultRouter()
router.register(r"committee-members", CommitteeMemberViewSet)
router.register(r"elections", ElectionViewSet)
router.register(r"candidates", CandidateViewSet)
router.register(r"subcommittees", SubCommitteeViewSet)
router.register(r"oath-records", OathRecordViewSet)
router.register(r"no-confidence-motions", NoConfidenceMotionViewSet)
router.register(r"handover-records", HandoverRecordViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
