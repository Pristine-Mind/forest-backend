from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.core.views import SystemConfigViewSet, UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"system-config", SystemConfigViewSet, basename="systemconfig")

urlpatterns = [
    path("", include(router.urls)),
]
