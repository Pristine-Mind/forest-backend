from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.forest.views import (
    ForestBlockViewSet,
    HarvestLogViewSet,
    OperationalPlanViewSet,
    PoleCountRegisterViewSet,
    SpeciesViewSet,
    TimberCollectionViewSet,
    TreeCountHistoryViewSet,
    TreeCountRegisterViewSet,
    WildlifeSpeciesViewSet,
)

router = DefaultRouter()
router.register(r"blocks", ForestBlockViewSet)
router.register(r"species", SpeciesViewSet)
router.register(r"wildlife-species", WildlifeSpeciesViewSet)
router.register(r"operational-plans", OperationalPlanViewSet)
router.register(r"tree-counts", TreeCountRegisterViewSet, basename="tree-counts")
router.register(r"tree-count-history", TreeCountHistoryViewSet, basename="tree-count-history")
router.register(r"harvest-logs", HarvestLogViewSet, basename="harvest-logs")
router.register(r"pole-counts", PoleCountRegisterViewSet, basename="pole-counts")
router.register(r"timber-collection", TimberCollectionViewSet, basename="timber-collections")

urlpatterns = [
    path("", include(router.urls)),
]
