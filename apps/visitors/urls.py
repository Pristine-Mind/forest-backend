from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.visitors.views import (
    OfficialGuestLogViewSet,
    VisitorEntryViewSet,
    VisitorFeeRateViewSet,
)

router = DefaultRouter()
router.register(r"fee-rates", VisitorFeeRateViewSet)
router.register(r"entries", VisitorEntryViewSet)
router.register(r"official-guests", OfficialGuestLogViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
