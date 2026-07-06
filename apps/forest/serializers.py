from rest_framework import serializers

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


class ForestBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForestBlock
        fields = [
            "id",
            "block_no",
            "block_name",
            "title",
            "total_area_ha",
            "productive_area_ha",
            "canopy_percent",
            "soil_types",
            "forest_type",
            "forest_condition",
            "major_species",
            "forest_management_activities",
            "non_timber_forest_products",
            "wildlife_species",
            "boundaries",
            "created_at",
            "updated_at",
        ]


class SpeciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Species
        fields = ["id", "species_name", "scientific_name", "local_name", "created_at", "updated_at"]


class WildlifeSpeciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = WildlifeSpecies
        fields = ["id", "species_name", "scientific_name", "local_name", "created_at", "updated_at"]


class OperationalPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationalPlan
        fields = [
            "id",
            "valid_from",
            "valid_to",
            "approved_harvest_limit",
            "description",
            "created_at",
            "updated_at",
        ]


class TreeCountRegisterSerializer(serializers.ModelSerializer):
    # Read-only fields for display
    block_name = serializers.CharField(source="block.block_name", read_only=True)
    species_name = serializers.CharField(source="species.species_name", read_only=True)
    tree_class_display = serializers.CharField(source="get_tree_class_display", read_only=True)

    class Meta:
        model = TreeCountRegister
        fields = [
            "id",
            # Relationships
            "block",
            "block_name",
            "operational_plan",
            "species",
            "species_name",
            # Plot information
            "plot_number",
            "tree_number",
            # Tree measurements
            "girth_cm",
            "height_m",
            "tree_class",
            "tree_class_display",
            # Volume calculations (auto-calculated, read-only)
            "basal_area_sqm",
            "stem_volume_cubic_m",
            "r_factor",
            "branch_volume_cubic_m",
            "total_volume_cubic_m",
            "r_less_than_10",
            "volume_less_than_10_cubic_m",
            "gross_volume_cubic_m",
            "net_volume_cubic_m",
            "fuelwood_volume_cubic_m",
            # Metadata
            "survey_date",
            "is_harvestable",
            "is_active",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "basal_area_sqm",
            "stem_volume_cubic_m",
            "r_factor",
            "branch_volume_cubic_m",
            "total_volume_cubic_m",
            "r_less_than_10",
            "volume_less_than_10_cubic_m",
            "gross_volume_cubic_m",
            "net_volume_cubic_m",
            "fuelwood_volume_cubic_m",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):
        """Validate unique together constraint"""
        # Only check for duplicates on create
        if self.instance is None:  # Create operation
            block = data.get("block")
            plot_number = data.get("plot_number")
            tree_number = data.get("tree_number")

            if block and plot_number and tree_number:
                if TreeCountRegister.objects.filter(block=block, plot_number=plot_number, tree_number=tree_number).exists():
                    raise serializers.ValidationError("A tree record already exists for this block, plot, and tree number.")
        return data

    def validate_girth_cm(self, value):
        """Validate girth measurement"""
        if value <= 0:
            raise serializers.ValidationError("Girth must be greater than 0.")
        if value > 500:
            raise serializers.ValidationError("Girth cannot exceed 500 cm.")
        return value

    def validate_height_m(self, value):
        """Validate height measurement"""
        if value <= 0:
            raise serializers.ValidationError("Height must be greater than 0.")
        if value > 100:
            raise serializers.ValidationError("Height cannot exceed 100 meters.")
        return value

    def validate_tree_class(self, value):
        """Validate tree class"""
        if value not in ["i", "ii", "iii"]:
            raise serializers.ValidationError("Tree class must be 'i', 'ii', or 'iii'.")
        return value


class TreeCountHistorySerializer(serializers.ModelSerializer):
    record_details = serializers.SerializerMethodField()

    class Meta:
        model = TreeCountHistory
        fields = [
            "id",
            "record",
            "record_details",
            "change_amount",
            "reference_harvest",
            "change_date",
            "note",
            "created_at",
        ]
        read_only_fields = ["record_details"]

    def get_record_details(self, obj):
        """Get details of the tree record"""
        return {
            "species": obj.record.species.species_name,
            "block": obj.record.block.block_name,
            "plot": f"{obj.record.plot_number}",
            "tree_number": obj.record.tree_number,
        }


class HarvestLogSerializer(serializers.ModelSerializer):
    tree_details = serializers.SerializerMethodField()

    class Meta:
        model = HarvestLog
        fields = [
            "id",
            "tree_record",
            "tree_details",
            "harvest_date",
            "harvest_quantity_cubic_m",
            "reference_harvest_request",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["tree_details"]

    def get_tree_details(self, obj):
        """Get details of the harvested tree"""
        return {
            "species": obj.tree_record.species.species_name,
            "block": obj.tree_record.block.block_name,
            "plot": f"{obj.tree_record.plot_number}",
            "tree_number": obj.tree_record.tree_number,
            "total_volume": obj.tree_record.total_volume_cubic_m,
            "net_volume": obj.tree_record.net_volume_cubic_m,
        }


class PlotSummarySerializer(serializers.Serializer):
    """Serializer for plot summary data"""

    total_trees = serializers.IntegerField()
    total_volume = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_net_volume = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_fuelwood = serializers.DecimalField(max_digits=10, decimal_places=2)
    species_count = serializers.IntegerField()
    average_height = serializers.DecimalField(max_digits=5, decimal_places=1)
    average_girth = serializers.DecimalField(max_digits=6, decimal_places=1)


class BlockSummarySerializer(serializers.Serializer):
    """Serializer for block summary data"""

    total_trees = serializers.IntegerField()
    total_plots = serializers.IntegerField()
    total_volume = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_net_volume = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_fuelwood = serializers.DecimalField(max_digits=10, decimal_places=2)
    species_list = serializers.ListField(child=serializers.CharField())
    average_height = serializers.DecimalField(max_digits=5, decimal_places=1)
    average_girth = serializers.DecimalField(max_digits=6, decimal_places=1)


class TimberCollectionSerializer(serializers.ModelSerializer):
    block_name = serializers.CharField(source="block.block_name", read_only=True)
    species_name = serializers.CharField(source="species.species_name", read_only=True)

    class Meta:
        model = TimberCollection
        fields = [
            "id",
            "block",
            "block_name",
            "species",
            "species_name",
            "wood_volume",
            "firewood",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, data):
        """Validate unique together constraint on create/update"""
        # Only check for duplicates on create
        if self.instance is None:  # Create operation
            block = data.get("block")
            species = data.get("species")

            if block and species:
                if TimberCollection.objects.filter(block=block, species=species).exists():
                    raise serializers.ValidationError(
                        "A timber collection record already exists for this block and species."
                    )
        return data


class PoleCountRegisterSerializer(serializers.ModelSerializer):
    # Read-only fields for display
    block_name = serializers.CharField(source="block.block_name", read_only=True, allow_null=True)
    species_name = serializers.CharField(source="species.species_name", read_only=True, allow_null=True)
    tree_class_display = serializers.CharField(source="get_tree_class_display", read_only=True)

    class Meta:
        model = PoleCountRegister
        fields = [
            "id",
            # Relationships
            "block",
            "block_name",
            "operational_plan",
            "species",
            "species_name",
            # Plot information
            "plot_number",
            "tree_number",
            # Tree measurements
            "girth_cm",
            "height_m",
            "tree_class",
            "tree_class_display",
            # Volume calculations (auto-calculated, read-only)
            "basal_area_sqm",
            "stem_volume_cubic_m",
            "r_factor",
            "branch_volume_cubic_m",
            "total_volume_cubic_m",
            "r_less_than_10",
            "volume_less_than_10_cubic_m",
            "gross_volume_cubic_m",
            "net_volume_cubic_m",
            "fuelwood_volume_cubic_m",
            # Metadata
            "survey_date",
            "is_harvestable",
            "is_active",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "basal_area_sqm",
            "stem_volume_cubic_m",
            "r_factor",
            "branch_volume_cubic_m",
            "total_volume_cubic_m",
            "r_less_than_10",
            "volume_less_than_10_cubic_m",
            "gross_volume_cubic_m",
            "net_volume_cubic_m",
            "fuelwood_volume_cubic_m",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):
        """Validate unique together constraint"""
        # Only check for duplicates on create
        if self.instance is None:  # Create operation
            block = data.get("block")
            plot_number = data.get("plot_number")
            tree_number = data.get("tree_number")

            # Validate required fields for unique constraint
            if not all([block, plot_number, tree_number]):
                raise serializers.ValidationError(
                    "block, plot_number, and tree_number are required for unique identification."
                )

            if PoleCountRegister.objects.filter(block=block, plot_number=plot_number, tree_number=tree_number).exists():
                raise serializers.ValidationError("A pole record already exists for this block, plot, and tree number.")
        return data

    def validate_girth_cm(self, value):
        """Validate girth measurement"""
        if value is not None:
            if value <= 0:
                raise serializers.ValidationError("Girth must be greater than 0.")
            if value > 500:
                raise serializers.ValidationError("Girth cannot exceed 500 cm.")
        return value

    def validate_height_m(self, value):
        """Validate height measurement"""
        if value is not None:
            if value <= 0:
                raise serializers.ValidationError("Height must be greater than 0.")
            if value > 100:
                raise serializers.ValidationError("Height cannot exceed 100 meters.")
        return value

    def validate_tree_class(self, value):
        """Validate tree class"""
        if value and value not in ["i", "ii", "iii"]:
            raise serializers.ValidationError("Tree class must be 'i', 'ii', or 'iii'.")
        return value

    def validate_plot_number(self, value):
        """Validate plot number"""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Plot number must be greater than 0.")
        return value

    def validate_tree_number(self, value):
        """Validate tree number"""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Tree number must be greater than 0.")
        return value


class ForestBoundarySerializer(serializers.ModelSerializer):
    geojson_feature = serializers.SerializerMethodField()

    class Meta:
        model = ForestBoundary
        fields = [
            "id",
            "name",
            "boundary_type",
            "forest_block",
            "coordinates",
            "description",
            "source_notes",
            "geojson_feature",
            "created_at",
            "updated_at",
        ]

    def get_geojson_feature(self, obj) -> dict:
        return obj.as_geojson_feature()


class ForestBoundaryInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForestBoundary
        fields = [
            "name",
            "boundary_type",
            "forest_block",
            "coordinates",
            "description",
            "source_notes",
        ]

    def validate_coordinates(self, value):
        if not isinstance(value, list) or len(value) < 4:
            raise serializers.ValidationError("coordinates must be a list of at least 4 [lng, lat] pairs.")
        for point in value:
            if not isinstance(point, list) or len(point) != 2:
                raise serializers.ValidationError("Each coordinate must be a [longitude, latitude] pair.")
        if value[0] != value[-1]:
            raise serializers.ValidationError("Polygon ring must be closed — first and last coordinate must be the same.")
        return value
