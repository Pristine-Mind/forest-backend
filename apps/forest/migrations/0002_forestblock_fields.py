# Generated migration for ForestBlock model updates

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("forest", "0001_initial"),  # Adjust this based on your actual migration
    ]

    operations = [
        migrations.AddField(
            model_name="forestblock",
            name="block_no",
            field=models.PositiveIntegerField(help_text="Block number", unique=True, null=True),
        ),
        migrations.AddField(
            model_name="forestblock",
            name="title",
            field=models.CharField(blank=True, help_text="Block title/description", max_length=500),
        ),
        migrations.AddField(
            model_name="forestblock",
            name="productive_area_ha",
            field=models.DecimalField(
                blank=True, decimal_places=2, help_text="Productive area in hectares (उत्पादक क्षेत्रफल)", max_digits=10, null=True, validators=[]
            ),
        ),
        migrations.AddField(
            model_name="forestblock",
            name="canopy_percent",
            field=models.DecimalField(
                blank=True, decimal_places=2, help_text="Canopy coverage percentage (छत्र आच्छादन प्रतिशत)", max_digits=5, null=True, validators=[]
            ),
        ),
        migrations.AddField(
            model_name="forestblock",
            name="soil_types",
            field=models.JSONField(blank=True, default=list, help_text="Soil types (माटोको प्रकार)"),
        ),
        migrations.AddField(
            model_name="forestblock",
            name="forest_type",
            field=models.CharField(blank=True, help_text="Forest type (वन प्रकार - प्राकृतिक/रोपित)", max_length=100),
        ),
        migrations.AddField(
            model_name="forestblock",
            name="forest_condition",
            field=models.CharField(blank=True, help_text="Forest condition (वन अवस्था)", max_length=100),
        ),
        migrations.AddField(
            model_name="forestblock",
            name="major_species",
            field=models.JSONField(blank=True, default=list, help_text="Major tree species (प्रमुख वृक्ष प्रजातिहरु)"),
        ),
        migrations.AddField(
            model_name="forestblock",
            name="forest_management_activities",
            field=models.JSONField(
                blank=True, default=list, help_text="Forest management activities (वन व्यवस्थापन गतिविधिहरु)"
            ),
        ),
        migrations.AddField(
            model_name="forestblock",
            name="non_timber_forest_products",
            field=models.JSONField(
                blank=True, default=list, help_text="Non-timber forest products (गैर-काठ वन उत्पादनहरु)"
            ),
        ),
        migrations.AddField(
            model_name="forestblock",
            name="wildlife_species",
            field=models.JSONField(blank=True, default=list, help_text="Wildlife species found in block (वन्यजन्तु प्रजातिहरु)"),
        ),
        migrations.AddField(
            model_name="forestblock",
            name="boundaries",
            field=models.JSONField(blank=True, default=dict, help_text="Block boundaries - {east, west, north, south} (सीमानाहरु)"),
        ),
        migrations.AlterField(
            model_name="forestblock",
            name="block_name",
            field=models.CharField(help_text="Block name (नाम)", max_length=255),
        ),
        migrations.AlterField(
            model_name="forestblock",
            name="area_hectares",
            field=models.DecimalField(
                decimal_places=2, help_text="Total area in hectares (कुल क्षेत्रफल हेक्टेयरमा)", max_digits=10, validators=[]
            ),
            preserve_default=False,
        ),
        migrations.RenameField(
            model_name="forestblock",
            old_name="area_hectares",
            new_name="total_area_ha",
        ),
        migrations.AlterModelOptions(
            name="forestblock",
            options={"ordering": ["block_no"], "verbose_name": "Forest Block", "verbose_name_plural": "Forest Blocks"},
        ),
    ]
