from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.members.views import (
    HouseholdDetailStatsViewSet,
    HouseholdStatsViewSet,
    HouseholdViewSet,
    MemberDetailStatsViewSet,
    MembershipRenewalViewSet,
    MemberViewSet,
    UserMemberStatsViewSet,
)

router = DefaultRouter()
router.register(r"households", HouseholdViewSet)
router.register(r"household-stats", HouseholdDetailStatsViewSet, basename="household-detail-stats")
router.register(r"members", MemberViewSet)
router.register(r"member-stats", MemberDetailStatsViewSet, basename="member-detail-stats")
router.register(r"membership-renewals", MembershipRenewalViewSet)
router.register(r"stats", HouseholdStatsViewSet, basename="household-stats")
router.register(r"user-stats", UserMemberStatsViewSet, basename="user-member-stats")

urlpatterns = [
    path("", include(router.urls)),
]
