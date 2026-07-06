from django.db.models import Avg, Sum
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import (
    IsAuthenticatedReadOnly,
    IsCommitteeOfficer,
)
from apps.forest.models import (
    ForestBlock,
    ForestBoundary,
    HarvestLog,
    OperationalPlan,
    PoleCountRegister,
    Species,
    TimberCollection,
    TreeCountHistory,
    TreeCountRegister,
    WildlifeSpecies,
)
from apps.forest.serializers import (
    BlockSummarySerializer,
    ForestBlockSerializer,
    ForestBoundarySerializer,
    HarvestLogSerializer,
    OperationalPlanSerializer,
    PlotSummarySerializer,
    PoleCountRegisterSerializer,
    SpeciesSerializer,
    TimberCollectionSerializer,
    TreeCountHistorySerializer,
    TreeCountRegisterSerializer,
    WildlifeSpeciesSerializer,
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
    search_fields = ["species_name", "scientific_name", "local_name"]


class WildlifeSpeciesViewSet(viewsets.ModelViewSet):
    queryset = WildlifeSpecies.objects.all()
    serializer_class = WildlifeSpeciesSerializer
    permission_classes = [IsCommitteeOfficer | IsAuthenticatedReadOnly]
    search_fields = ["species_name", "scientific_name", "local_name"]


class OperationalPlanViewSet(viewsets.ModelViewSet):
    queryset = OperationalPlan.objects.all()
    serializer_class = OperationalPlanSerializer
    permission_classes = [IsCommitteeOfficer | IsAuthenticatedReadOnly]
    filterset_fields = ["valid_from", "valid_to"]


class TreeCountRegisterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Tree Count Register records.
    Provides CRUD operations and summary endpoints.
    """

    queryset = TreeCountRegister.objects.select_related("operational_plan", "species").all()
    serializer_class = TreeCountRegisterSerializer
    permission_classes = [IsCommitteeOfficer | IsAuthenticatedReadOnly]

    # Filtering and searching
    filterset_fields = [
        "block",
        "operational_plan",
        "species",
        "tree_class",
        "is_harvestable",
        "is_active",
        "plot_number",
    ]
    search_fields = ["block__block_name", "species__species_name", "notes"]
    ordering_fields = ["plot_number", "tree_number", "girth_cm", "height_m", "total_volume_cubic_m", "created_at"]
    ordering = ["block__block_name", "plot_number", "tree_number"]

    @action(detail=False, methods=["get"], url_path="plot-summary")
    def plot_summary(self, request):
        """
        Get summary for a specific plot.
        Query Parameters:
            - block_id: ID of the block
            - plot_number: Plot number
        """
        block_id = request.query_params.get("block_id")
        plot_number = request.query_params.get("plot_number")

        if not all([block_id, plot_number]):
            return Response({"error": "block_id and plot_number are required"}, status=status.HTTP_400_BAD_REQUEST)

        trees = self.get_queryset().filter(block_id=block_id, plot_number=plot_number, is_active=True)

        if not trees.exists():
            return Response({"error": "No trees found for this plot"}, status=status.HTTP_404_NOT_FOUND)

        summary = {
            "block_id": int(block_id),
            "plot_number": int(plot_number),
            "total_trees": trees.count(),
            "total_volume": trees.aggregate(Sum("total_volume_cubic_m"))["total_volume_cubic_m__sum"] or 0,
            "total_net_volume": trees.aggregate(Sum("net_volume_cubic_m"))["net_volume_cubic_m__sum"] or 0,
            "total_fuelwood": trees.aggregate(Sum("fuelwood_volume_cubic_m"))["fuelwood_volume_cubic_m__sum"] or 0,
            "species_count": trees.values("species").distinct().count(),
            "average_height": trees.aggregate(Avg("height_m"))["height_m__avg"] or 0,
            "average_girth": trees.aggregate(Avg("girth_cm"))["girth_cm__avg"] or 0,
            "trees": TreeCountRegisterSerializer(trees, many=True).data,
        }

        return Response(summary)

    @action(detail=False, methods=["get"], url_path="section-summary")
    def section_summary(self, request):
        """
        Get summary for a specific section.
        Query Parameters:
            - block_id: ID of the block
        """
        block_id = request.query_params.get("block_id")

        if not block_id:
            return Response({"error": "block_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        trees = self.get_queryset().filter(block_id=block_id, is_active=True)

        if not trees.exists():
            return Response({"error": "No trees found for this section"}, status=status.HTTP_404_NOT_FOUND)

        summary = {
            "block_id": int(block_id),
            "total_trees": trees.count(),
            "total_plots": trees.values("plot_number").distinct().count(),
            "total_volume": trees.aggregate(Sum("total_volume_cubic_m"))["total_volume_cubic_m__sum"] or 0,
            "total_net_volume": trees.aggregate(Sum("net_volume_cubic_m"))["net_volume_cubic_m__sum"] or 0,
            "total_fuelwood": trees.aggregate(Sum("fuelwood_volume_cubic_m"))["fuelwood_volume_cubic_m__sum"] or 0,
            "species_count": trees.values("species").distinct().count(),
            "average_height": trees.aggregate(Avg("height_m"))["height_m__avg"] or 0,
            "average_girth": trees.aggregate(Avg("girth_cm"))["girth_cm__avg"] or 0,
        }

        return Response(summary)

    @action(detail=False, methods=["get"], url_path="block-summary")
    def block_summary(self, request):
        """
        Get summary for a complete block.
        Query Parameters:
            - block_id: ID of the block
            - operational_plan_id: (Optional) Filter by operational plan
        """
        block_id = request.query_params.get("block_id")
        operational_plan_id = request.query_params.get("operational_plan_id")

        if not block_id:
            return Response({"error": "block_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            block = ForestBlock.objects.get(id=block_id)
        except ForestBlock.DoesNotExist:
            return Response({"error": "Block not found"}, status=status.HTTP_404_NOT_FOUND)

        trees = self.get_queryset().filter(block_id=block_id, is_active=True)

        if operational_plan_id:
            trees = trees.filter(operational_plan_id=operational_plan_id)

        if not trees.exists():
            return Response({"error": "No trees found for this block"}, status=status.HTTP_404_NOT_FOUND)

        summary = {
            "block_id": block.id,
            "block_name": block.block_name,
            "total_trees": trees.count(),
            "total_sections": trees.values("section").distinct().count(),
            "total_plots": trees.values("plot_number").distinct().count(),
            "total_volume": trees.aggregate(Sum("total_volume_cubic_m"))["total_volume_cubic_m__sum"] or 0,
            "total_net_volume": trees.aggregate(Sum("net_volume_cubic_m"))["net_volume_cubic_m__sum"] or 0,
            "total_fuelwood": trees.aggregate(Sum("fuelwood_volume_cubic_m"))["fuelwood_volume_cubic_m__sum"] or 0,
            "species_count": trees.values("species").distinct().count(),
            "species_list": list(trees.values_list("species__species_name", flat=True).distinct()),
            "average_height": trees.aggregate(Avg("height_m"))["height_m__avg"] or 0,
            "average_girth": trees.aggregate(Avg("girth_cm"))["girth_cm__avg"] or 0,
            "class_i_count": trees.filter(tree_class="i").count(),
            "class_ii_count": trees.filter(tree_class="ii").count(),
            "class_iii_count": trees.filter(tree_class="iii").count(),
            "harvestable_count": trees.filter(is_harvestable=True).count(),
            "non_harvestable_count": trees.filter(is_harvestable=False).count(),
        }

        return Response(summary)

    @action(detail=False, methods=["get"], url_path="species-distribution")
    def species_distribution(self, request):
        """
        Get species distribution across sections.
        Query Parameters:
            - block_id: ID of the block
            - operational_plan_id: (Optional) Filter by operational plan
        """
        block_id = request.query_params.get("block_id")
        operational_plan_id = request.query_params.get("operational_plan_id")

        if not block_id:
            return Response({"error": "block_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        trees = self.get_queryset().filter(block_id=block_id, is_active=True)

        if operational_plan_id:
            trees = trees.filter(operational_plan_id=operational_plan_id)

        if not trees.exists():
            return Response({"error": "No trees found for this block"}, status=status.HTTP_404_NOT_FOUND)

        # Group by species and plot
        distribution = {}

        for tree in trees:
            species_name = tree.species.species_name
            plot_number = tree.plot_number
            if species_name not in distribution:
                distribution[species_name] = {
                    "species_id": tree.species.id,
                    "species_name": species_name,
                    "total_trees": 0,
                    "total_volume": 0,
                    "sections": {},
                }

            distribution[species_name]["total_trees"] += 1
            distribution[species_name]["total_volume"] += float(tree.total_volume_cubic_m or 0)

            if plot_number not in distribution[species_name]["sections"]:
                distribution[species_name]["sections"][plot_number] = 0
            distribution[species_name]["sections"][plot_number] += 1

        # Convert to list and sort
        result = list(distribution.values())
        result.sort(key=lambda x: x["total_trees"], reverse=True)

        return Response(result)

    @action(detail=False, methods=["post"], url_path="bulk-create")
    def bulk_create(self, request):
        """
        Bulk create tree records.
        """
        data = request.data

        if not isinstance(data, list):
            return Response({"error": "Expected a list of records"}, status=status.HTTP_400_BAD_REQUEST)

        if len(data) > 100:
            return Response({"error": "Maximum 100 records allowed per bulk operation"}, status=status.HTTP_400_BAD_REQUEST)

        created = []
        errors = []

        for index, item in enumerate(data):
            serializer = TreeCountRegisterSerializer(data=item)
            if serializer.is_valid():
                try:
                    tree = serializer.save()
                    created.append(
                        {
                            "index": index,
                            "id": tree.id,
                            "block": tree.block.block_name,
                            "plot": tree.plot_number,
                            "tree_number": tree.tree_number,
                            "species": tree.species.species_name,
                        }
                    )
                except Exception as e:
                    errors.append({"index": index, "error": str(e)})
            else:
                errors.append({"index": index, "errors": serializer.errors})

        response_data = {
            "created": created,
            "errors": errors,
            "total_processed": len(data),
            "total_created": len(created),
            "total_errors": len(errors),
        }

        if errors:
            return Response(response_data, status=status.HTTP_207_MULTI_STATUS)
        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="by-plot")
    def get_by_plot(self, request):
        """
        Get all trees in a specific plot.
        Query Parameters:
            - block_id: ID of the block
            - section_id: ID of the section
            - plot_number: Plot number
        """
        block_id = request.query_params.get("block_id")
        section_id = request.query_params.get("section_id")
        plot_number = request.query_params.get("plot_number")

        if not all([block_id, section_id, plot_number]):
            return Response(
                {"error": "block_id, section_id, and plot_number are required"}, status=status.HTTP_400_BAD_REQUEST
            )

        trees = self.get_queryset().filter(block_id=block_id, section_id=section_id, plot_number=plot_number, is_active=True)

        serializer = self.get_serializer(trees, many=True)
        return Response(serializer.data)


class TreeCountHistoryViewSet(viewsets.ModelViewSet):
    queryset = TreeCountHistory.objects.select_related("record", "record__species", "record__block", "reference_harvest")
    serializer_class = TreeCountHistorySerializer
    permission_classes = [IsCommitteeOfficer | IsAuthenticatedReadOnly]
    filterset_fields = ["record", "change_date", "record__block", "record__species"]
    ordering_fields = ["change_date"]


class HarvestLogViewSet(viewsets.ModelViewSet):
    queryset = HarvestLog.objects.select_related(
        "tree_record", "tree_record__species", "tree_record__block", "reference_harvest_request"
    )
    serializer_class = HarvestLogSerializer
    permission_classes = [IsCommitteeOfficer | IsAuthenticatedReadOnly]
    filterset_fields = ["tree_record", "harvest_date", "tree_record__block", "tree_record__species"]
    ordering_fields = ["harvest_date"]


class TimberCollectionViewSet(viewsets.ModelViewSet):
    queryset = TimberCollection.objects.select_related("block", "species").all()
    serializer_class = TimberCollectionSerializer
    permission_classes = [IsCommitteeOfficer | IsAuthenticatedReadOnly]

    # Filtering and searching
    filterset_fields = ["block", "species"]
    search_fields = ["block__block_name", "species__species_name"]
    ordering_fields = ["block__block_name", "species__species_name", "wood_volume", "firewood"]
    ordering = ["block__block_name", "species__species_name"]

    @action(detail=False, methods=["get"], url_path="block-summary")
    def block_summary(self, request):
        """
        Get timber collection summary by block.
        Query Parameters:
            - block_id: ID of the block to summarize
        """
        block_id = request.query_params.get("block_id")

        if not block_id:
            return Response({"error": "block_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            block = ForestBlock.objects.get(id=block_id)
        except ForestBlock.DoesNotExist:
            return Response({"error": "Block not found"}, status=status.HTTP_404_NOT_FOUND)

        collections = self.get_queryset().filter(block_id=block_id)

        summary = {
            "block_id": block.id,
            "block_name": block.block_name,
            "total_species": collections.count(),
            "total_wood_volume": collections.aggregate(Sum("wood_volume"))["wood_volume__sum"] or 0,
            "total_firewood": collections.aggregate(Sum("firewood"))["firewood__sum"] or 0,
            "species": [],
        }

        for collection in collections:
            summary["species"].append(
                {
                    "species_id": collection.species.id,
                    "species_name": collection.species.species_name,
                    "wood_volume": collection.wood_volume,
                    "firewood": collection.firewood,
                }
            )

        return Response(summary)

    @action(detail=False, methods=["get"], url_path="species-summary")
    def species_summary(self, request):
        """
        Get timber collection summary by species.
        Query Parameters:
            - species_id: ID of the species to summarize
        """
        species_id = request.query_params.get("species_id")

        if not species_id:
            return Response({"error": "species_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        collections = self.get_queryset().filter(species_id=species_id)

        if not collections.exists():
            return Response({"error": "No collections found for this species"}, status=status.HTTP_404_NOT_FOUND)

        species = collections.first().species

        summary = {
            "species_id": species.id,
            "species_name": species.species_name,
            "total_blocks": collections.count(),
            "total_wood_volume": collections.aggregate(Sum("wood_volume"))["wood_volume__sum"] or 0,
            "total_firewood": collections.aggregate(Sum("firewood"))["firewood__sum"] or 0,
            "blocks": [],
        }

        for collection in collections:
            summary["blocks"].append(
                {
                    "block_id": collection.block.id,
                    "block_name": collection.block.block_name,
                    "wood_volume": collection.wood_volume,
                    "firewood": collection.firewood,
                }
            )

        return Response(summary)

    @action(detail=False, methods=["get"], url_path="total-summary")
    def total_summary(self, request):
        """
        Get overall summary of all timber collections.
        """
        queryset = self.get_queryset()

        summary = {
            "total_blocks": queryset.values("block").distinct().count(),
            "total_species": queryset.values("species").distinct().count(),
            "total_records": queryset.count(),
            "total_wood_volume": queryset.aggregate(Sum("wood_volume"))["wood_volume__sum"] or 0,
            "total_firewood": queryset.aggregate(Sum("firewood"))["firewood__sum"] or 0,
        }

        return Response(summary)

    @action(detail=False, methods=["post"], url_path="bulk-create")
    def bulk_create(self, request):
        """
        Bulk create timber collection records.
        """
        data = request.data

        if not isinstance(data, list):
            return Response({"error": "Expected a list of records"}, status=status.HTTP_400_BAD_REQUEST)

        if len(data) > 100:
            return Response({"error": "Maximum 100 records allowed per bulk operation"}, status=status.HTTP_400_BAD_REQUEST)

        created = []
        errors = []

        for index, item in enumerate(data):
            serializer = TimberCollectionSerializer(data=item)
            if serializer.is_valid():
                try:
                    collection = serializer.save()
                    created.append(
                        {
                            "index": index,
                            "id": collection.id,
                            "block": collection.block.block_name,
                            "species": collection.species.species_name,
                        }
                    )
                except Exception as e:
                    errors.append({"index": index, "error": str(e)})
            else:
                errors.append({"index": index, "errors": serializer.errors})

        response_data = {
            "created": created,
            "errors": errors,
            "total_processed": len(data),
            "total_created": len(created),
            "total_errors": len(errors),
        }

        if errors:
            return Response(response_data, status=status.HTTP_207_MULTI_STATUS)
        return Response(response_data, status=status.HTTP_201_CREATED)


class PoleCountRegisterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Pole Count Register records.
    Provides CRUD operations and summary endpoints.
    """

    queryset = PoleCountRegister.objects.select_related("block", "operational_plan", "species").all()
    serializer_class = PoleCountRegisterSerializer
    permission_classes = [IsCommitteeOfficer | IsAuthenticatedReadOnly]

    # Filtering and searching
    filterset_fields = [
        "block",
        "operational_plan",
        "species",
        "plot_number",
        "tree_class",
        "is_harvestable",
        "is_active",
    ]
    search_fields = ["block__block_name", "species__species_name", "notes"]
    ordering_fields = ["plot_number", "tree_number", "girth_cm", "height_m", "total_volume_cubic_m", "created_at"]
    ordering = ["block__block_name", "plot_number", "tree_number"]

    @action(detail=False, methods=["get"], url_path="plot-summary")
    def plot_summary(self, request):
        """
        Get summary for a specific plot.
        Query Parameters:
            - block_id: ID of the block
            - plot_number: Plot number
        """
        block_id = request.query_params.get("block_id")
        plot_number = request.query_params.get("plot_number")

        if not all([block_id, plot_number]):
            return Response({"error": "block_id and plot_number are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plot_number = int(plot_number)
        except ValueError:
            return Response({"error": "plot_number must be an integer"}, status=status.HTTP_400_BAD_REQUEST)

        poles = self.get_queryset().filter(block_id=block_id, plot_number=plot_number, is_active=True)

        if not poles.exists():
            return Response({"error": "No poles found for this plot"}, status=status.HTTP_404_NOT_FOUND)

        summary = {
            "block_id": int(block_id),
            "plot_number": plot_number,
            "total_poles": poles.count(),
            "total_volume": poles.aggregate(Sum("total_volume_cubic_m"))["total_volume_cubic_m__sum"] or 0,
            "total_net_volume": poles.aggregate(Sum("net_volume_cubic_m"))["net_volume_cubic_m__sum"] or 0,
            "total_fuelwood": poles.aggregate(Sum("fuelwood_volume_cubic_m"))["fuelwood_volume_cubic_m__sum"] or 0,
            "species_count": poles.values("species").distinct().count(),
            "average_height": poles.aggregate(Avg("height_m"))["height_m__avg"] or 0,
            "average_girth": poles.aggregate(Avg("girth_cm"))["girth_cm__avg"] or 0,
            "poles": PoleCountRegisterSerializer(poles, many=True).data,
        }

        return Response(summary)

    @action(detail=False, methods=["get"], url_path="plot-summary")
    def plot_summary(self, request):
        """
        Get summary for a specific plot.
        Query Parameters:
            - block_id: ID of the block
            - plot_number: Plot number
        """
        block_id = request.query_params.get("block_id")
        plot_number = request.query_params.get("plot_number")

        if not all([block_id, plot_number]):
            return Response({"error": "block_id and plot_number are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plot_number = int(plot_number)
        except ValueError:
            return Response({"error": "plot_number must be an integer"}, status=status.HTTP_400_BAD_REQUEST)

        poles = self.get_queryset().filter(block_id=block_id, plot_number=plot_number, is_active=True)

        if not poles.exists():
            return Response({"error": "No poles found for this plot"}, status=status.HTTP_404_NOT_FOUND)

        summary = {
            "block_id": int(block_id),
            "plot_number": plot_number,
            "total_poles": poles.count(),
            "total_plots": poles.values("plot_number").distinct().count(),
            "total_volume": poles.aggregate(Sum("total_volume_cubic_m"))["total_volume_cubic_m__sum"] or 0,
            "total_net_volume": poles.aggregate(Sum("net_volume_cubic_m"))["net_volume_cubic_m__sum"] or 0,
            "total_fuelwood": poles.aggregate(Sum("fuelwood_volume_cubic_m"))["fuelwood_volume_cubic_m__sum"] or 0,
            "species_count": poles.values("species").distinct().count(),
            "average_height": poles.aggregate(Avg("height_m"))["height_m__avg"] or 0,
            "average_girth": poles.aggregate(Avg("girth_cm"))["girth_cm__avg"] or 0,
            "harvestable_count": poles.filter(is_harvestable=True).count(),
            "non_harvestable_count": poles.filter(is_harvestable=False).count(),
        }

        return Response(summary)

    @action(detail=False, methods=["get"], url_path="block-summary")
    def block_summary(self, request):
        """
        Get summary for a complete block.
        Query Parameters:
            - block_id: ID of the block
            - operational_plan_id: (Optional) Filter by operational plan
        """
        block_id = request.query_params.get("block_id")
        operational_plan_id = request.query_params.get("operational_plan_id")

        if not block_id:
            return Response({"error": "block_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            block = ForestBlock.objects.get(id=block_id)
        except ForestBlock.DoesNotExist:
            return Response({"error": "Block not found"}, status=status.HTTP_404_NOT_FOUND)

        poles = self.get_queryset().filter(block_id=block_id, is_active=True)

        if operational_plan_id:
            poles = poles.filter(operational_plan_id=operational_plan_id)

        if not poles.exists():
            return Response({"error": "No poles found for this block"}, status=status.HTTP_404_NOT_FOUND)

        summary = {
            "block_id": block.id,
            "block_name": block.block_name,
            "total_poles": poles.count(),
            "total_plots": poles.values("plot_number").distinct().count(),
            "total_volume": poles.aggregate(Sum("total_volume_cubic_m"))["total_volume_cubic_m__sum"] or 0,
            "total_net_volume": poles.aggregate(Sum("net_volume_cubic_m"))["net_volume_cubic_m__sum"] or 0,
            "total_fuelwood": poles.aggregate(Sum("fuelwood_volume_cubic_m"))["fuelwood_volume_cubic_m__sum"] or 0,
            "species_count": poles.values("species").distinct().count(),
            "species_list": list(poles.values_list("species__species_name", flat=True).distinct()),
            "average_height": poles.aggregate(Avg("height_m"))["height_m__avg"] or 0,
            "average_girth": poles.aggregate(Avg("girth_cm"))["girth_cm__avg"] or 0,
            "class_i_count": poles.filter(tree_class="i").count(),
            "class_ii_count": poles.filter(tree_class="ii").count(),
            "class_iii_count": poles.filter(tree_class="iii").count(),
            "harvestable_count": poles.filter(is_harvestable=True).count(),
            "non_harvestable_count": poles.filter(is_harvestable=False).count(),
            "active_count": poles.filter(is_active=True).count(),
            "archived_count": poles.filter(is_active=False).count(),
        }

        return Response(summary)

    @action(detail=False, methods=["get"], url_path="species-distribution")
    def species_distribution(self, request):
        """
        Get species distribution across plots.
        Query Parameters:
            - block_id: ID of the block
            - operational_plan_id: (Optional) Filter by operational plan
        """
        block_id = request.query_params.get("block_id")
        operational_plan_id = request.query_params.get("operational_plan_id")

        if not block_id:
            return Response({"error": "block_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        poles = self.get_queryset().filter(block_id=block_id, is_active=True)

        if operational_plan_id:
            poles = poles.filter(operational_plan_id=operational_plan_id)

        if not poles.exists():
            return Response({"error": "No poles found for this block"}, status=status.HTTP_404_NOT_FOUND)

        # Group by species and section
        distribution = {}

        for pole in poles:
            species_name = pole.species.species_name if pole.species else "Unknown"
            plot_number = pole.plot_number

            if species_name not in distribution:
                distribution[species_name] = {
                    "species_id": pole.species.id if pole.species else None,
                    "species_name": species_name,
                    "total_poles": 0,
                    "total_volume": 0,
                    "sections": {},
                }

            distribution[species_name]["total_poles"] += 1
            distribution[species_name]["total_volume"] += float(pole.total_volume_cubic_m or 0)

            if plot_number not in distribution[species_name]["sections"]:
                distribution[species_name]["sections"][plot_number] = 0
            distribution[species_name]["sections"][plot_number] += 1

        # Convert to list and sort
        result = list(distribution.values())
        result.sort(key=lambda x: x["total_poles"], reverse=True)

        return Response(result)

    @action(detail=False, methods=["get"], url_path="class-distribution")
    def class_distribution(self, request):
        """
        Get tree class distribution.
        Query Parameters:
            - block_id: ID of the block (optional)
        """
        poles = self.get_queryset().filter(is_active=True)

        block_id = request.query_params.get("block_id")

        if block_id:
            poles = poles.filter(block_id=block_id)

        plot_number = request.query_params.get("plot_number")
        if plot_number:
            try:
                poles = poles.filter(plot_number=int(plot_number))
            except ValueError:
                return Response({"error": "plot_number must be an integer"}, status=status.HTTP_400_BAD_REQUEST)

        if not poles.exists():
            return Response({"error": "No poles found"}, status=status.HTTP_404_NOT_FOUND)

        distribution = {
            "class_i": poles.filter(tree_class="i").count(),
            "class_ii": poles.filter(tree_class="ii").count(),
            "class_iii": poles.filter(tree_class="iii").count(),
            "unclassified": poles.filter(tree_class__isnull=True).count(),
            "total": poles.count(),
            "class_i_percentage": 0,
            "class_ii_percentage": 0,
            "class_iii_percentage": 0,
        }

        total = distribution["total"]
        if total > 0:
            distribution["class_i_percentage"] = round((distribution["class_i"] / total) * 100, 2)
            distribution["class_ii_percentage"] = round((distribution["class_ii"] / total) * 100, 2)
            distribution["class_iii_percentage"] = round((distribution["class_iii"] / total) * 100, 2)

        return Response(distribution)

    @action(detail=False, methods=["post"], url_path="bulk-create")
    def bulk_create(self, request):
        """
        Bulk create pole records.
        """
        data = request.data

        if not isinstance(data, list):
            return Response({"error": "Expected a list of records"}, status=status.HTTP_400_BAD_REQUEST)

        if len(data) > 100:
            return Response({"error": "Maximum 100 records allowed per bulk operation"}, status=status.HTTP_400_BAD_REQUEST)

        created = []
        errors = []

        for index, item in enumerate(data):
            serializer = PoleCountRegisterSerializer(data=item)
            if serializer.is_valid():
                try:
                    pole = serializer.save()
                    created.append(
                        {
                            "index": index,
                            "id": pole.id,
                            "block": pole.block.block_name if pole.block else None,
                            "plot": pole.plot_number,
                            "tree_number": pole.tree_number,
                            "species": pole.species.species_name if pole.species else None,
                        }
                    )
                except Exception as e:
                    errors.append({"index": index, "error": str(e)})
            else:
                errors.append({"index": index, "errors": serializer.errors})

        response_data = {
            "created": created,
            "errors": errors,
            "total_processed": len(data),
            "total_created": len(created),
            "total_errors": len(errors),
        }

        if errors:
            return Response(response_data, status=status.HTTP_207_MULTI_STATUS)
        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="by-plot")
    def get_by_plot(self, request):
        """
        Get all poles in a specific plot.
        Query Parameters:
            - block_id: ID of the block
            - plot_number: Plot number
        """
        block_id = request.query_params.get("block_id")
        plot_number = request.query_params.get("plot_number")

        if not all([block_id, plot_number]):
            return Response({"error": "block_id and plot_number are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plot_number = int(plot_number)
        except ValueError:
            return Response({"error": "plot_number must be an integer"}, status=status.HTTP_400_BAD_REQUEST)

        poles = self.get_queryset().filter(block_id=block_id, plot_number=plot_number, is_active=True)

        serializer = self.get_serializer(poles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="by-plot")
    def get_by_plot(self, request):
        """
        Get all trees in a specific plot.
        Query Parameters:
            - block_id: ID of the block
            - section_id: ID of the section
            - plot_number: Plot number
        """
        block_id = request.query_params.get("block_id")
        section_id = request.query_params.get("section_id")
        plot_number = request.query_params.get("plot_number")

        if not all([block_id, section_id, plot_number]):
            return Response(
                {"error": "block_id, section_id, and plot_number are required"}, status=status.HTTP_400_BAD_REQUEST
            )

        trees = self.get_queryset().filter(block_id=block_id, section_id=section_id, plot_number=plot_number, is_active=True)

        serializer = self.get_serializer(trees, many=True)
        return Response(serializer.data)


class ForestBoundaryViewSet(viewsets.ModelViewSet):
    queryset = ForestBoundary.objects.select_related("forest_block")
    permission_classes = [IsCommitteeOfficer | IsAuthenticatedReadOnly]
    filterset_fields = ["boundary_type", "forest_block"]

    def get_serializer_class(self):
        return ForestBoundarySerializer

    @action(detail=False, methods=["get"])
    def geojson(self, request):
        """
        Returns a GeoJSON FeatureCollection of all boundaries.
        """
        qs = self.get_queryset()
        return Response(
            {
                "type": "FeatureCollection",
                "features": [obj.as_geojson_feature() for obj in qs],
            }
        )
