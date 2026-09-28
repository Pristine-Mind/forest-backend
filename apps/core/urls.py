from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.core.views import AuthViewSet, ChangePasswordView, SystemConfigViewSet, UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"system-config", SystemConfigViewSet, basename="systemconfig")
router.register(r"auth", AuthViewSet, basename="auth")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/change-password/", ChangePasswordView.as_view(), name="change-password"),
]
