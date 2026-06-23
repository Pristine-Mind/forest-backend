from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.members.views import (
    HouseholdViewSet,
    MembershipRenewalViewSet,
    MemberViewSet,
)

router = DefaultRouter()
router.register(r"households", HouseholdViewSet)
router.register(r"members", MemberViewSet)
router.register(r"membership-renewals", MembershipRenewalViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
