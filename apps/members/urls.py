from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.members.views import (
    HouseholdViewSet,
    MemberDetailStatsViewSet,
    MembershipRenewalViewSet,
    MemberStatsViewSet,
    MemberViewSet,
    UserMemberStatsViewSet,
)

router = DefaultRouter()
router.register(r"households", HouseholdViewSet)
router.register(r"members", MemberViewSet)
router.register(r"members-stats", MemberDetailStatsViewSet, basename="member-detail-stats")
router.register(r"membership-renewals", MembershipRenewalViewSet)
router.register(r"stats", MemberStatsViewSet, basename="member-stats")
router.register(r"user-stats", UserMemberStatsViewSet, basename="user-member-stats")

urlpatterns = [
    path("", include(router.urls)),
]
