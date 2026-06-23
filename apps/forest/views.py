from rest_framework import viewsets

from apps.core.permissions import (
    IsAuthenticatedReadOnly,
    IsCommitteeOfficer,
)
from apps.forest.models import ForestBlock, OperationalPlan, Species, TreeCountRegister
from apps.forest.serializers import (
    ForestBlockSerializer,
    OperationalPlanSerializer,
    SpeciesSerializer,
    TreeCountRegisterSerializer,
)


class ForestBlockViewSet(viewsets.ModelViewSet):
    queryset = ForestBlock.objects.all()
    serializer_class = ForestBlockSerializer
    permission_classes = [IsCommitteeOfficer | IsAuthenticatedReadOnly]
    filterset_fields = ["block_name"]
    search_fields = ["block_name"]


class SpeciesViewSet(viewsets.ModelViewSet):
    queryset = Species.objects.all()
    serializer_class = SpeciesSerializer
    permission_classes = [IsCommitteeOfficer | IsAuthenticatedReadOnly]
    search_fields = ["species_name"]


class OperationalPlanViewSet(viewsets.ModelViewSet):
    queryset = OperationalPlan.objects.all()
    serializer_class = OperationalPlanSerializer
    permission_classes = [IsCommitteeOfficer | IsAuthenticatedReadOnly]
    filterset_fields = ["valid_from", "valid_to"]


class TreeCountRegisterViewSet(viewsets.ModelViewSet):
    queryset = TreeCountRegister.objects.select_related("species", "block")
    serializer_class = TreeCountRegisterSerializer
    permission_classes = [IsCommitteeOfficer | IsAuthenticatedReadOnly]
    filterset_fields = ["species", "block"]
    search_fields = ["species__species_name", "block__block_name"]
