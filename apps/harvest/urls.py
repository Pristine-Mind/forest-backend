from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.harvest.views import HarvestRequestViewSet

router = DefaultRouter()
router.register(r"requests", HarvestRequestViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
