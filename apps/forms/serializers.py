from datetime import date, datetime

from rest_framework import serializers

from .models import (
    CuttingRegister,
    CuttingRegisterItem,
    FellingRegister,
    FellingRegisterEntry,
    ForestProductReceipt,
    ForestProductReceiptItem,
    TreeSurveyForm,
    TreeSurveyFormItem,
)


class TreeSurveyFormItemSerializer(serializers.ModelSerializer):
    """Serializer for individual tree items in survey form"""

    species_name = serializers.CharField(source="species.species_name", read_only=True)

    class Meta:
        model = TreeSurveyFormItem
        fields = [
            "id",
            "serial_number",
            "species",
            "species_name",
            "girth_cm",
            "height_m",
            "volume_cubic_m",
            "fuelwood_volume_cubic_m",
            "wood_type",
            "remarks",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TreeSurveyFormSerializer(serializers.ModelSerializer):
    """Serializer for tree survey forms with nested items creation support"""

    tree_items = TreeSurveyFormItemSerializer(many=True, read_only=True)
    block_name = serializers.CharField(source="block.block_name", read_only=True)
    total_volume = serializers.SerializerMethodField()
    total_fuelwood = serializers.SerializerMethodField()

    # Writable nested field for creation
    tree_items_data = TreeSurveyFormItemSerializer(
        source="tree_items",
        many=True,
        write_only=True,
        required=False,
        help_text="Array of tree items to create with the form",
    )

    class Meta:
        model = TreeSurveyForm
        fields = [
            "id",
            "form_number",
            "survey_date",
            "block",
            "block_name",
            "operational_plan",
            "district",
            "municipality",
            "ward_number",
            "plot_number",
            "forest_category",
            "community_representative",
            "community_representative_sign_date",
            "forest_officer",
            "forest_officer_sign_date",
            "tree_items",
            "tree_items_data",
            "total_volume",
            "total_fuelwood",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "total_volume", "total_fuelwood", "tree_items"]

    def get_total_volume(self, obj):
        """Calculate total volume"""
        return obj.get_total_volume()

    def get_total_fuelwood(self, obj):
        """Calculate total fuelwood"""
        return obj.get_total_fuelwood()

    def create(self, validated_data):
        """Create survey form with nested tree items"""
        tree_items_data = validated_data.pop("tree_items", [])

        # Create the survey form
        survey_form = TreeSurveyForm.objects.create(**validated_data)

        # Create the tree items
        for item_data in tree_items_data:
            TreeSurveyFormItem.objects.create(survey_form=survey_form, **item_data)

        return survey_form

    def update(self, instance, validated_data):
        """Update survey form and handle tree items if provided"""
        tree_items_data = validated_data.pop("tree_items", None)

        # Update the survey form fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # If tree_items_data is provided, create new items
        if tree_items_data is not None:
            # Optional: Delete existing items or just add new ones
            # instance.tree_items.all().delete()  # Uncomment to replace all items
            for item_data in tree_items_data:
                TreeSurveyFormItem.objects.create(survey_form=instance, **item_data)

        return instance


class CuttingRegisterItemSerializer(serializers.ModelSerializer):
    """Serializer for individual cutting register items"""

    species_name = serializers.CharField(source="species.species_name", read_only=True)

    class Meta:
        model = CuttingRegisterItem
        fields = [
            "id",
            "serial_number",
            "entry_time",
            "plot_number",
            "quota_number",
            "species",
            "species_name",
            "size_measurement",
            "volume_cubic_m",
            "comments",
            "remarks",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CuttingRegisterSerializer(serializers.ModelSerializer):
    """Serializer for cutting registers with nested items creation support"""

    cutting_items = CuttingRegisterItemSerializer(many=True, read_only=True)
    block_name = serializers.CharField(source="block.block_name", read_only=True)
    total_volume = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()

    # Writable nested field for creation
    cutting_items_data = CuttingRegisterItemSerializer(
        source="cutting_items",
        many=True,
        write_only=True,
        required=False,
        help_text="Array of cutting items to create with the register",
    )

    class Meta:
        model = CuttingRegister
        fields = [
            "id",
            "form_number",
            "register_date",
            "block",
            "block_name",
            "operational_plan",
            "zone",
            "district",
            "municipality",
            "ward_number",
            "forest_classification",
            "block_plot_name",
            "block_plot_type",
            "cutting_location",
            "community_representative_name",
            "community_representative_position",
            "community_representative_sign_date",
            "forest_officer_name",
            "forest_officer_position",
            "forest_officer_sign_date",
            "cutting_items",
            "cutting_items_data",
            "total_volume",
            "item_count",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "total_volume", "item_count", "cutting_items"]

    def get_total_volume(self, obj):
        """Calculate total volume"""
        return obj.get_total_volume()

    def get_item_count(self, obj):
        """Get item count"""
        return obj.get_item_count()

    def create(self, validated_data):
        """Create cutting register with nested items"""
        cutting_items_data = validated_data.pop("cutting_items", [])

        # Create the cutting register
        cutting_register = CuttingRegister.objects.create(**validated_data)

        # Create the cutting items
        for item_data in cutting_items_data:
            CuttingRegisterItem.objects.create(cutting_register=cutting_register, **item_data)

        return cutting_register

    def update(self, instance, validated_data):
        """Update cutting register and handle items if provided"""
        cutting_items_data = validated_data.pop("cutting_items", None)

        # Update the cutting register fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # If cutting_items_data is provided, create new items
        if cutting_items_data is not None:
            # Optional: Delete existing items or just add new ones
            # instance.cutting_items.all().delete()  # Uncomment to replace all items
            for item_data in cutting_items_data:
                CuttingRegisterItem.objects.create(cutting_register=instance, **item_data)

        return instance


class FellingRegisterEntrySerializer(serializers.ModelSerializer):
    species_name = serializers.CharField(source="species.species_name", read_only=True)

    class Meta:
        model = FellingRegisterEntry
        fields = [
            "id",
            "register",
            "entry_date",
            "entry_time",
            "rawana_number",
            "golia_number",
            "species",
            "species_name",
            "measurement_size",
            "volume_cubic_feet",
            "firewood_chatta",
            "remarks",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {"register": {"required": False}}


class FellingRegisterSerializer(serializers.ModelSerializer):

    entries = FellingRegisterEntrySerializer(many=True, required=False)

    class Meta:
        model = FellingRegister
        fields = [
            "id",
            "area",
            "district",
            "sub_division",
            "block_name_and_type",
            "felling_location",
            "cutting_agency_name",
            "tree_count",
            "felling_sawing_deadline",
            "dispatch_deadline",
            "cfug_rep_name",
            "cfug_rep_position",
            "cfug_rep_signed_date",
            "forest_rep_name",
            "forest_rep_position",
            "forest_rep_signed_date",
            "entries",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def create(self, validated_data):
        entries_data = validated_data.pop("entries", [])
        register = FellingRegister.objects.create(**validated_data)
        for entry_data in entries_data:
            FellingRegisterEntry.objects.create(register=register, **entry_data)
        return register

    def update(self, instance, validated_data):
        entries_data = validated_data.pop("entries", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if entries_data is not None:
            instance.entries.all().delete()
            for entry_data in entries_data:
                FellingRegisterEntry.objects.create(register=instance, **entry_data)

        return instance


class ForestProductReceiptItemSerializer(serializers.ModelSerializer):
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = ForestProductReceiptItem
        fields = [
            "id",
            "product_name",
            "grade",
            "unit",
            "quantity",
            "rate_per_unit",
            "total_amount",
            "remarks",
        ]
        extra_kwargs = {
            "rate_per_unit": {"required": True},
            "quantity": {"required": True},
            "unit": {"required": True},
            "product_name": {"required": True},
        }


class ForestProductReceiptSerializer(serializers.ModelSerializer):
    items = ForestProductReceiptItemSerializer(many=True, required=True)
    grand_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = ForestProductReceipt
        fields = [
            "id",
            "receipt_no",
            "cfug_registration_no",
            "buyer_name",
            "buyer_address",
            "issue_date",
            "sales",
            "receiver_name",
            "receiver_date",
            "issuer_name",
            "issuer_position",
            "issuer_date",
            "items",
            "grand_total",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "issue_date": {"required": True},
            "buyer_name": {"required": True},
            "receipt_no": {"required": True},
        }

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        sales = validated_data.pop("sales", [])
        # Set issue_date to current date if not provided
        if "issue_date" not in validated_data or validated_data["issue_date"] is None:
            validated_data["issue_date"] = date.today()
        receipt = ForestProductReceipt.objects.create(**validated_data)
        if sales:
            receipt.sales.set(sales)
        for item_data in items_data:
            ForestProductReceiptItem.objects.create(receipt=receipt, **item_data)
        return receipt

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        sales = validated_data.pop("sales", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if sales is not None:
            instance.sales.set(sales)
        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                ForestProductReceiptItem.objects.create(receipt=instance, **item_data)
        return instance
