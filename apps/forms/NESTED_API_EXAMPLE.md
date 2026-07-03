# Nested API Examples - Survey Forms and Cutting Registers

## Creating Survey Form with Multiple Items in One API Call

### POST `/api/v1/survey-forms/`

```json
{
  "form_number": "SURVEY-001",
  "survey_date": "2026-07-03",
  "block": 1,
  "district": "Kathmandu",
  "municipality": "Chandragiri",
  "ward_number": 5,
  "plot_number": 101,
  "forest_category": "Community Forest",
  "community_representative": "Ram Prasad Sharma",
  "forest_officer": "Hari Singh",
  "notes": "Survey completed successfully",
  "tree_items_data": [
    {
      "serial_number": 1,
      "species": 1,
      "girth_cm": 45.5,
      "height_m": 15.2,
      "volume_cubic_m": 2.45,
      "fuelwood_volume_cubic_m": 0.5,
      "wood_type": "timber",
      "remarks": "Good quality timber"
    },
    {
      "serial_number": 2,
      "species": 2,
      "girth_cm": 38.3,
      "height_m": 12.8,
      "volume_cubic_m": 1.85,
      "fuelwood_volume_cubic_m": 0.3,
      "wood_type": "timber",
      "remarks": "Medium quality"
    },
    {
      "serial_number": 3,
      "species": 3,
      "girth_cm": 30.0,
      "height_m": 10.5,
      "volume_cubic_m": 1.2,
      "fuelwood_volume_cubic_m": 0.8,
      "wood_type": "fuelwood",
      "remarks": "Fuelwood harvest"
    }
  ]
}
```

### Response (201 Created)

```json
{
  "id": 1,
  "form_number": "SURVEY-001",
  "survey_date": "2026-07-03",
  "block": 1,
  "block_name": "Shivapuri Block",
  "operational_plan": null,
  "district": "Kathmandu",
  "municipality": "Chandragiri",
  "ward_number": 5,
  "plot_number": 101,
  "forest_category": "Community Forest",
  "community_representative": "Ram Prasad Sharma",
  "community_representative_sign_date": null,
  "forest_officer": "Hari Singh",
  "forest_officer_sign_date": null,
  "tree_items": [
    {
      "id": 1,
      "serial_number": 1,
      "species": 1,
      "species_name": "Sal",
      "girth_cm": "45.5",
      "height_m": "15.2",
      "volume_cubic_m": "2.450",
      "fuelwood_volume_cubic_m": "0.500",
      "wood_type": "timber",
      "remarks": "Good quality timber",
      "created_at": "2026-07-03T10:30:00Z",
      "updated_at": "2026-07-03T10:30:00Z"
    },
    {
      "id": 2,
      "serial_number": 2,
      "species": 2,
      "species_name": "Katus",
      "girth_cm": "38.3",
      "height_m": "12.8",
      "volume_cubic_m": "1.850",
      "fuelwood_volume_cubic_m": "0.300",
      "wood_type": "timber",
      "remarks": "Medium quality",
      "created_at": "2026-07-03T10:30:00Z",
      "updated_at": "2026-07-03T10:30:00Z"
    },
    {
      "id": 3,
      "serial_number": 3,
      "species": 3,
      "species_name": "Chir",
      "girth_cm": "30.0",
      "height_m": "10.5",
      "volume_cubic_m": "1.200",
      "fuelwood_volume_cubic_m": "0.800",
      "wood_type": "fuelwood",
      "remarks": "Fuelwood harvest",
      "created_at": "2026-07-03T10:30:00Z",
      "updated_at": "2026-07-03T10:30:00Z"
    }
  ],
  "total_volume": 5.5,
  "total_fuelwood": 1.6,
  "notes": "Survey completed successfully",
  "created_at": "2026-07-03T10:30:00Z",
  "updated_at": "2026-07-03T10:30:00Z"
}
```

---

## Creating Cutting Register with Multiple Items in One API Call

### POST `/api/v1/cutting-registers/`

```json
{
  "form_number": "CUT-001",
  "register_date": "2026-07-03",
  "block": 1,
  "zone": "Eastern Zone",
  "district": "Kathmandu",
  "municipality": "Chandragiri",
  "ward_number": 5,
  "forest_classification": "Community Forest",
  "block_plot_name": "Block A",
  "block_plot_type": "Natural Forest",
  "cutting_location": "Northern slope",
  "community_representative_name": "Ram Prasad",
  "forest_officer_name": "Hari Singh",
  "notes": "Cutting operation completed",
  "cutting_items_data": [
    {
      "serial_number": 1,
      "entry_time": "09:00:00",
      "plot_number": "P101",
      "quota_number": "Q001",
      "species": 1,
      "size_measurement": "45.5cm x 15.2m",
      "volume_cubic_m": 2.45,
      "comments": "First batch",
      "remarks": "Quality timber"
    },
    {
      "serial_number": 2,
      "entry_time": "10:30:00",
      "plot_number": "P102",
      "quota_number": "Q002",
      "species": 2,
      "size_measurement": "38.3cm x 12.8m",
      "volume_cubic_m": 1.85,
      "comments": "Second batch",
      "remarks": "Medium quality"
    },
    {
      "serial_number": 3,
      "entry_time": "13:00:00",
      "plot_number": "P103",
      "quota_number": "Q003",
      "species": 3,
      "size_measurement": "30.0cm x 10.5m",
      "volume_cubic_m": 1.2,
      "comments": "Fuelwood batch",
      "remarks": "Harvested for fuel"
    }
  ]
}
```

### Response (201 Created)

```json
{
  "id": 1,
  "form_number": "CUT-001",
  "register_date": "2026-07-03",
  "block": 1,
  "block_name": "Shivapuri Block",
  "operational_plan": null,
  "zone": "Eastern Zone",
  "district": "Kathmandu",
  "municipality": "Chandragiri",
  "ward_number": 5,
  "forest_classification": "Community Forest",
  "block_plot_name": "Block A",
  "block_plot_type": "Natural Forest",
  "cutting_location": "Northern slope",
  "community_representative_name": "Ram Prasad",
  "community_representative_position": null,
  "community_representative_sign_date": null,
  "forest_officer_name": "Hari Singh",
  "forest_officer_position": null,
  "forest_officer_sign_date": null,
  "cutting_items": [
    {
      "id": 1,
      "serial_number": 1,
      "entry_time": "09:00:00",
      "plot_number": "P101",
      "quota_number": "Q001",
      "species": 1,
      "species_name": "Sal",
      "size_measurement": "45.5cm x 15.2m",
      "volume_cubic_m": "2.450",
      "comments": "First batch",
      "remarks": "Quality timber",
      "created_at": "2026-07-03T10:35:00Z",
      "updated_at": "2026-07-03T10:35:00Z"
    },
    {
      "id": 2,
      "serial_number": 2,
      "entry_time": "10:30:00",
      "plot_number": "P102",
      "quota_number": "Q002",
      "species": 2,
      "species_name": "Katus",
      "size_measurement": "38.3cm x 12.8m",
      "volume_cubic_m": "1.850",
      "comments": "Second batch",
      "remarks": "Medium quality",
      "created_at": "2026-07-03T10:35:00Z",
      "updated_at": "2026-07-03T10:35:00Z"
    },
    {
      "id": 3,
      "serial_number": 3,
      "entry_time": "13:00:00",
      "plot_number": "P103",
      "quota_number": "Q003",
      "species": 3,
      "species_name": "Chir",
      "size_measurement": "30.0cm x 10.5m",
      "volume_cubic_m": "1.200",
      "comments": "Fuelwood batch",
      "remarks": "Harvested for fuel",
      "created_at": "2026-07-03T10:35:00Z",
      "updated_at": "2026-07-03T10:35:00Z"
    }
  ],
  "total_volume": 5.5,
  "item_count": 3,
  "notes": "Cutting operation completed",
  "created_at": "2026-07-03T10:35:00Z",
  "updated_at": "2026-07-03T10:35:00Z"
}
```

---

## Usage Notes

### Key Points:

1. **Field Names**: Use `tree_items_data` for survey forms and `cutting_items_data` for cutting registers when creating with nested items
2. **Response**: The response will include the nested items in `tree_items` and `cutting_items` fields (not the `_data` versions)
3. **Automatic Calculations**: The API automatically calculates `total_volume`, `total_fuelwood` (for surveys), and `item_count`
4. **Validation**: All standard validation applies to both parent and nested items
5. **Transactions**: All items are created together - if any validation fails, the entire request fails

### Without Nested Items:

You can also create just the form/register without items:

```json
{
  "form_number": "SURVEY-002",
  "survey_date": "2026-07-04",
  "block": 1,
  "district": "Kathmandu",
  "municipality": "Chandragiri",
  "ward_number": 5,
  "plot_number": 102,
  "forest_category": "Community Forest"
}
```

Then add items separately using the item endpoints or update the form with items later.

### Updating with New Items:

When updating a form/register (PUT/PATCH), providing `tree_items_data` or `cutting_items_data` will create additional items. Use:

```bash
PATCH /api/v1/survey-forms/{id}/
```

```json
{
  "tree_items_data": [
    {
      "serial_number": 4,
      "species": 1,
      "girth_cm": 50.0,
      "height_m": 16.0,
      "volume_cubic_m": 3.0,
      "fuelwood_volume_cubic_m": 0.2,
      "wood_type": "timber"
    }
  ]
}
```

---

## Filtering and Searching

Both endpoints support:

```bash
# Filter by block
GET /api/v1/survey-forms/?block=1

# Filter by date
GET /api/v1/survey-forms/?survey_date=2026-07-03

# Search by form number
GET /api/v1/survey-forms/?search=SURVEY-001

# Combine filters
GET /api/v1/survey-forms/?block=1&survey_date=2026-07-03
```

## PDF Export

Export individual forms as PDF:

```bash
GET /api/v1/survey-forms/{id}/pdf/
GET /api/v1/cutting-registers/{id}/pdf/
```
