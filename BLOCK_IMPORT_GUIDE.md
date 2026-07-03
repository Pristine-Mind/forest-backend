# Forest Block Data Import Guide

## Overview
This guide explains how to import forest block data from the `data/block.json` file into the Django database.

## File Structure
The `block.json` file contains a JSON array of forest block objects with the following structure:

```json
[
  {
    "block_no": 1,
    "title": "Block Title",
    "boundaries": {
      "east": "Description",
      "west": "Description",
      "north": "Description",
      "south": "Description"
    },
    "total_area_ha": 542.46,
    "productive_area_ha": 434.91,
    "canopy_percent": 60.70,
    "soil": ["Type 1", "Type 2"],
    "forest_type": "प्राकृतिक",
    "forest_condition": "राम्रो",
    "major_species": ["Species 1", "Species 2"],
    "forest_management_activities": ["Activity 1", "Activity 2"],
    "non_timber_forest_products": ["Product 1", "Product 2"],
    "wildlife": ["Wildlife 1", "Wildlife 2"]
  }
]
```

## Fields Description

| Field | Type | Description | Nepali | Required |
|-------|------|-------------|--------|----------|
| block_no | Integer | Unique block number | खण्ड नं. | Yes |
| title | String | Block title/description | शीर्षक | No |
| total_area_ha | Decimal | Total area in hectares | कुल क्षेत्रफल हेक्टेयरमा | Yes |
| productive_area_ha | Decimal | Productive area in hectares | उत्पादक क्षेत्रफल | No |
| canopy_percent | Decimal | Canopy coverage percentage | छत्र आच्छादन प्रतिशत | No |
| soil_types | Array | Array of soil type names | माटोको प्रकार | No |
| forest_type | String | Forest type (Natural/Planted) | वन प्रकार | No |
| forest_condition | String | Forest condition status | वन अवस्था | No |
| major_species | Array | Major tree species found | प्रमुख वृक्ष प्रजातिहरु | No |
| forest_management_activities | Array | Management activities | वन व्यवस्थापन गतिविधिहरु | No |
| non_timber_forest_products | Array | Non-timber products | गैर-काठ वन उत्पादनहरु | No |
| wildlife_species | Array | Wildlife species found | वन्यजन्तु प्रजातिहरु | No |
| boundaries | Object | Block boundaries (east, west, north, south) | सीमानाहरु | No |

## Database Models

### ForestBlock Model
The ForestBlock model stores all block information with the following key fields:

- `block_no`: Unique identifier for the block
- `block_name`: Name of the block
- `title`: Descriptive title
- `total_area_ha`: Total area in hectares
- `productive_area_ha`: Productive area in hectares
- `canopy_percent`: Canopy coverage percentage
- `soil_types`: JSON array of soil types
- `forest_type`: Type of forest
- `forest_condition`: Condition of the forest
- `major_species`: JSON array of major species
- `forest_management_activities`: JSON array of management activities
- `non_timber_forest_products`: JSON array of NTFP
- `wildlife_species`: JSON array of wildlife
- `boundaries`: JSON object containing boundary descriptions

## Import Instructions

### Step 1: Prepare the Data
Ensure your `data/block.json` file is in the correct format with all required fields.

### Step 2: Run Database Migrations
First, apply the migrations to create/update the ForestBlock table:

```bash
python manage.py migrate forest
```

### Step 3: Import the Data

#### Basic Import
```bash
python manage.py import_blocks
```

#### Import with Specific File Path
```bash
python manage.py import_blocks --file /path/to/blocks.json
```

#### Clear Existing Data and Re-import
```bash
python manage.py import_blocks --clear
```

### Step 4: Verify Import
Check the admin panel to verify that all blocks have been imported correctly:

```
http://your-server/admin/forest/forestblock/
```

## API Endpoints

### Get All Blocks
```
GET /api/v1/forest/blocks/
```

### Get Specific Block
```
GET /api/v1/forest/blocks/{id}/
```

### Create Block
```
POST /api/v1/forest/blocks/
Content-Type: application/json

{
  "block_no": 1,
  "block_name": "Block 1",
  "title": "Description",
  "total_area_ha": "542.46",
  "productive_area_ha": "434.91",
  "canopy_percent": "60.70",
  "soil_types": ["काळो", "फुस्रो"],
  "forest_type": "प्राकृतिक",
  "forest_condition": "राम्रो",
  "major_species": ["साल", "जामुन"],
  "forest_management_activities": ["झाडी सफाइ"],
  "non_timber_forest_products": ["बेत"],
  "wildlife_species": ["बाँदर"],
  "boundaries": {
    "east": "Description",
    "west": "Description",
    "north": "Description",
    "south": "Description"
  }
}
```

### Update Block
```
PATCH /api/v1/forest/blocks/{id}/
```

### Delete Block
```
DELETE /api/v1/forest/blocks/{id}/
```

## Troubleshooting

### Issue: "File not found"
**Solution**: Ensure the file path is correct and the file exists:
```bash
ls -la data/block.json
```

### Issue: "Invalid JSON format"
**Solution**: Validate the JSON file:
```bash
python -m json.tool data/block.json
```

### Issue: "Unique constraint violation on block_no"
**Solution**: Use the `--clear` option to remove existing blocks:
```bash
python manage.py import_blocks --clear
```

### Issue: DecimalField validation error
**Solution**: Ensure all numeric values are strings in the JSON and properly formatted:
```json
{
  "total_area_ha": "542.46",
  "canopy_percent": "60.70"
}
```

## Backup and Export

### Export Current Blocks to JSON
```bash
python manage.py dumpdata forest.ForestBlock --format=json --indent=2 > blocks_backup.json
```

### Restore from Backup
```bash
python manage.py loaddata blocks_backup.json
```

## Additional Notes

- All areas are stored in hectares (ha)
- Canopy percentage should be between 0-100
- JSON arrays are used for storing multiple values
- The import command uses `update_or_create` to handle both new and existing blocks
- Timestamps (`created_at`, `updated_at`) are automatically managed by Django
