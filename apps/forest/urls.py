from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.forest.views import (
    ForestBlockViewSet,
    OperationalPlanViewSet,
    SpeciesViewSet,
    TreeCountRegisterViewSet,
)

router = DefaultRouter()
router.register(r"blocks", ForestBlockViewSet)
router.register(r"species", SpeciesViewSet)
router.register(r"operational-plans", OperationalPlanViewSet)
router.register(r"tree-counts", TreeCountRegisterViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
