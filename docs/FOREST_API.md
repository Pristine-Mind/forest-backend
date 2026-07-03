# Forest App API Documentation

**Base URL:** `/api/forest/`  
**API Version:** 1.0  
**Last Updated:** July 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication & Permissions](#authentication--permissions)
3. [Data Types](#data-types)
4. [API Endpoints](#api-endpoints)
   - [Forest Blocks](#forest-blocks)
   - [Species](#species)
   - [Wildlife Species](#wildlife-species)
   - [Operational Plans](#operational-plans)
   - [Tree Count Register](#tree-count-register)
   - [Tree Count History](#tree-count-history)
   - [Harvest Logs](#harvest-logs)
   - [Pole Count Register](#pole-count-register)
   - [Timber Collection](#timber-collection)
5. [Error Handling](#error-handling)
6. [Common Patterns](#common-patterns)

---

## Overview

The Forest App API provides comprehensive management for forest inventory tracking, tree measurements, species management, and harvest logging. It supports:

- **Forest Block Management** - Track forest subdivisions
- **Species Inventory** - Manage tree and wildlife species
- **Tree Count Register** - Detailed tree measurements with auto-calculated volumes
- **Operational Planning** - Define harvest limits and timelines
- **Harvest Tracking** - Log harvested trees and maintain history
- **Pole Count Register** - Track poles separately from main trees
- **Timber Collection** - Manage timber collection data by species and block

---

## Authentication & Permissions

### Authentication
All endpoints require Bearer token authentication via JWT.

```
Authorization: Bearer <your_jwt_token>
```

### Permission Levels

| Role | Permissions |
|------|------------|
| **CommitteeOfficer** | Full CRUD access (Create, Read, Update, Delete) |
| **AuthenticatedUser** | Read-only access |
| **Anonymous** | No access |

### Headers Required

```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

---

## Data Types

### Core Models & Serializers

#### 1. ForestBlock

Represents a subdivision of forest area.

```json
{
  "id": 1,
  "block_name": "Block A",
  "area_hectares": "150.50",
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-01-15T10:30:00Z"
}
```

**Fields:**
- `id` (integer, read-only) - Unique identifier
- `block_name` (string, required, max 255) - Name of the forest block
- `area_hectares` (decimal) - Total area in hectares (must be ≥ 0)
- `created_at` (datetime, read-only) - Creation timestamp
- `updated_at` (datetime, read-only) - Last update timestamp

---

#### 2. Species

Represents tree species in the forest.

```json
{
  "id": 1,
  "species_name": "Sal",
  "scientific_name": "Shorea robusta",
  "local_name": "सालको रुख",
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-01-15T10:30:00Z"
}
```

**Fields:**
- `id` (integer, read-only) - Unique identifier
- `species_name` (string, required, max 255, unique) - Common species name
- `scientific_name` (string, optional, max 255) - Scientific/Latin name
- `local_name` (string, optional, max 255) - Local language name
- `created_at` (datetime, read-only)
- `updated_at` (datetime, read-only)

---

#### 3. WildlifeSpecies

Represents wildlife species found in the forest.

```json
{
  "id": 1,
  "species_name": "Tiger",
  "scientific_name": "Panthera tigris",
  "local_name": "बाघ",
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-01-15T10:30:00Z"
}
```

**Fields:** Same as Species

---

#### 4. OperationalPlan

Defines forest management plans with harvest limits and validity periods.

```json
{
  "id": 1,
  "valid_from": "2026-01-01",
  "valid_to": "2030-12-31",
  "approved_harvest_limit": "5000.00",
  "description": "5-year operational plan for sustainable harvest",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

**Fields:**
- `id` (integer, read-only)
- `valid_from` (date, required) - Plan start date
- `valid_to` (date, required) - Plan end date
- `approved_harvest_limit` (decimal, required) - Maximum harvestable volume in cubic meters (≥ 0)
- `description` (text, optional) - Plan details
- `created_at` (datetime, read-only)
- `updated_at` (datetime, read-only)

---

#### 5. TreeCountRegister

Detailed tree inventory with auto-calculated volume metrics.

```json
{
  "id": 1,
  "block": 1,
  "block_name": "Block A",
  "operational_plan": 1,
  "species": 1,
  "species_name": "Sal",
  "plot_number": 1,
  "tree_number": 5,
  "girth_cm": "120.5",
  "height_m": "25.3",
  "tree_class": "i",
  "tree_class_display": "I",
  "basal_area_sqm": "1.1547",
  "stem_volume_cubic_m": "13.0905",
  "r_factor": "0.00",
  "branch_volume_cubic_m": "0.0000",
  "total_volume_cubic_m": "13.0905",
  "r_less_than_10": "0.00",
  "volume_less_than_10_cubic_m": "0.000",
  "gross_volume_cubic_m": "12.4359",
  "net_volume_cubic_m": "9.9487",
  "fuelwood_volume_cubic_m": "4.3526",
  "survey_date": "2026-01-15",
  "is_harvestable": true,
  "is_active": true,
  "notes": "Healthy tree, good condition",
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-01-15T10:30:00Z"
}
```

**Fields:**

*Required Fields (for create/update):*
- `block` (integer, required) - Forest block ID
- `operational_plan` (integer, optional) - Operational plan ID
- `species` (integer, required) - Species ID
- `plot_number` (integer, required) - Plot number (> 0)
- `tree_number` (integer, required) - Sequence number in plot (> 0)
- `girth_cm` (decimal, required) - Girth at breast height in cm (0 < value ≤ 500)
- `height_m` (decimal, required) - Tree height in meters (0 < value ≤ 100)
- `tree_class` (string, required) - One of: "i", "ii", "iii"

*Auto-Calculated Fields (read-only):*
- `basal_area_sqm` - Basal area in square meters
- `stem_volume_cubic_m` - Stem volume (Basal Area × Height × Form Factor 0.45)
- `r_factor` - Branch ratio factor (varies by tree class)
- `branch_volume_cubic_m` - Branch volume (Stem Volume × R Factor)
- `total_volume_cubic_m` - Total volume (Stem + Branch)
- `r_less_than_10` - Small diameter R factor
- `volume_less_than_10_cubic_m` - Volume for trees < 10cm diameter
- `gross_volume_cubic_m` - Total × 0.95 (5% bark loss)
- `net_volume_cubic_m` - Gross × 0.80 (20% waste factor)
- `fuelwood_volume_cubic_m` - Gross × 0.35 (fuelwood portion)

*Optional Fields:*
- `survey_date` (date) - Date of measurement
- `is_harvestable` (boolean, default: true) - Whether tree can be harvested
- `is_active` (boolean, default: true) - Whether record is active
- `notes` (text) - Additional notes

*Metadata (read-only):*
- `created_at`, `updated_at` - Timestamps

**Validation Rules:**
- Girth must be between 0 and 500 cm
- Height must be between 0 and 100 meters
- Tree class must be "i", "ii", or "iii"
- Unique constraint on: (block, plot_number, tree_number)

---

#### 6. TreeCountHistory

Historical tracking of tree count changes.

```json
{
  "id": 1,
  "record": 5,
  "record_details": {
    "species": "Sal",
    "block": "Block A",
    "plot": "1",
    "tree_number": 5
  },
  "change_amount": 10,
  "reference_harvest": 1,
  "change_date": "2026-02-20",
  "note": "Harvested in batch",
  "created_at": "2026-02-20T14:30:00Z"
}
```

**Fields:**
- `id` (integer, read-only)
- `record` (integer, required) - TreeCountRegister ID
- `record_details` (object, read-only) - Nested tree information
- `change_amount` (integer, required) - Number of trees changed (> 0)
- `reference_harvest` (integer, optional) - HarvestRequest ID reference
- `change_date` (date, required) - Date of change
- `note` (text, optional) - Change notes
- `created_at` (datetime, read-only)

---

#### 7. HarvestLog

Log of harvested trees.

```json
{
  "id": 1,
  "tree_record": 5,
  "tree_details": {
    "species": "Sal",
    "block": "Block A",
    "plot": "1",
    "tree_number": 5,
    "total_volume": "13.0905",
    "net_volume": "9.9487"
  },
  "harvest_date": "2026-02-20",
  "harvest_quantity_cubic_m": "9.95",
  "reference_harvest_request": 1,
  "notes": "Successfully harvested",
  "created_at": "2026-02-20T14:30:00Z",
  "updated_at": "2026-02-20T14:30:00Z"
}
```

**Fields:**
- `id` (integer, read-only)
- `tree_record` (integer, required) - TreeCountRegister ID
- `tree_details` (object, read-only) - Nested tree information
- `harvest_date` (date, required) - Date of harvest
- `harvest_quantity_cubic_m` (decimal, required) - Harvested volume in cubic meters (≥ 0)
- `reference_harvest_request` (integer, optional) - HarvestRequest ID reference
- `notes` (text, optional) - Harvest notes
- `created_at`, `updated_at` (datetime, read-only)

---

#### 8. PoleCountRegister

Similar to TreeCountRegister but specifically for poles.

```json
{
  "id": 1,
  "block": 1,
  "block_name": "Block A",
  "operational_plan": 1,
  "species": 1,
  "species_name": "Sal",
  "plot_number": 2,
  "tree_number": 3,
  "girth_cm": "80.0",
  "height_m": "18.5",
  "tree_class": "ii",
  "tree_class_display": "II",
  "basal_area_sqm": "0.5099",
  "stem_volume_cubic_m": "3.7237",
  "r_factor": "0.15",
  "branch_volume_cubic_m": "0.5586",
  "total_volume_cubic_m": "4.2823",
  "r_less_than_10": "0.00",
  "volume_less_than_10_cubic_m": "0.000",
  "gross_volume_cubic_m": "4.0681",
  "net_volume_cubic_m": "3.2545",
  "fuelwood_volume_cubic_m": "1.4238",
  "survey_date": "2026-01-20",
  "is_harvestable": true,
  "is_active": true,
  "notes": "Pole inventory",
  "created_at": "2026-01-20T10:30:00Z",
  "updated_at": "2026-01-20T10:30:00Z"
}
```

**Fields:** Same structure as TreeCountRegister

---

#### 9. TimberCollection

Aggregate timber collection data by block and species.

```json
{
  "id": 1,
  "block": 1,
  "block_name": "Block A",
  "species": 1,
  "species_name": "Sal",
  "wood_volume": "1500.75",
  "firewood": "400.25",
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-01-15T10:30:00Z"
}
```

**Fields:**
- `id` (integer, read-only)
- `block` (integer, required) - Forest block ID
- `block_name` (string, read-only) - Block name
- `species` (integer, required) - Species ID
- `species_name` (string, read-only) - Species name
- `wood_volume` (decimal, required) - Total wood volume in cubic meters
- `firewood` (decimal, required) - Firewood volume in cubic meters
- `created_at`, `updated_at` (datetime, read-only)

**Validation:**
- Unique constraint on: (block, species)

---

## API Endpoints

### Forest Blocks

#### List Forest Blocks
```
GET /api/forest/blocks/
```

**Query Parameters:**
- `block_name` (string) - Filter by block name
- `page` (integer) - Pagination page number
- `limit` (integer) - Results per page (default: 20)

**Response:**
```json
{
  "count": 5,
  "next": "http://api.example.com/api/forest/blocks/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "block_name": "Block A",
      "area_hectares": "150.50",
      "created_at": "2026-01-15T10:30:00Z",
      "updated_at": "2026-01-15T10:30:00Z"
    }
  ]
}
```

---

#### Create Forest Block
```
POST /api/forest/blocks/
```

**Permission:** CommitteeOfficer required

**Request Body:**
```json
{
  "block_name": "Block B",
  "area_hectares": "200.00"
}
```

**Response (201 Created):**
```json
{
  "id": 2,
  "block_name": "Block B",
  "area_hectares": "200.00",
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-01-15T10:30:00Z"
}
```

---

#### Retrieve Forest Block
```
GET /api/forest/blocks/{id}/
```

**Response:**
```json
{
  "id": 1,
  "block_name": "Block A",
  "area_hectares": "150.50",
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-01-15T10:30:00Z"
}
```

---

#### Update Forest Block
```
PUT /api/forest/blocks/{id}/
PATCH /api/forest/blocks/{id}/
```

**Permission:** CommitteeOfficer required

**Request Body (PATCH):**
```json
{
  "block_name": "Block A Updated"
}
```

---

#### Delete Forest Block
```
DELETE /api/forest/blocks/{id}/
```

**Permission:** CommitteeOfficer required

---

### Species

#### List Species
```
GET /api/forest/species/
```

**Query Parameters:**
- `search` (string) - Search in species_name, scientific_name, local_name
- `page` (integer)
- `limit` (integer)

**Response:**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "species_name": "Sal",
      "scientific_name": "Shorea robusta",
      "local_name": "सालको रुख",
      "created_at": "2026-01-15T10:30:00Z",
      "updated_at": "2026-01-15T10:30:00Z"
    }
  ]
}
```

---

#### Create Species
```
POST /api/forest/species/
```

**Permission:** CommitteeOfficer required

**Request Body:**
```json
{
  "species_name": "Pine",
  "scientific_name": "Pinus roxburghii",
  "local_name": "चीड"
}
```

---

#### Retrieve Species
```
GET /api/forest/species/{id}/
```

---

#### Update Species
```
PUT /api/forest/species/{id}/
PATCH /api/forest/species/{id}/
```

**Permission:** CommitteeOfficer required

---

#### Delete Species
```
DELETE /api/forest/species/{id}/
```

**Permission:** CommitteeOfficer required

---

### Wildlife Species

#### List Wildlife Species
```
GET /api/forest/wildlife-species/
```

**Query Parameters:** Same as Species

**Response:** Same structure as Species

---

#### Create Wildlife Species
```
POST /api/forest/wildlife-species/
```

**Permission:** CommitteeOfficer required

---

#### Retrieve Wildlife Species
```
GET /api/forest/wildlife-species/{id}/
```

---

#### Update Wildlife Species
```
PUT /api/forest/wildlife-species/{id}/
PATCH /api/forest/wildlife-species/{id}/
```

**Permission:** CommitteeOfficer required

---

#### Delete Wildlife Species
```
DELETE /api/forest/wildlife-species/{id}/
```

**Permission:** CommitteeOfficer required

---

### Operational Plans

#### List Operational Plans
```
GET /api/forest/operational-plans/
```

**Query Parameters:**
- `valid_from` (date) - Filter by start date
- `valid_to` (date) - Filter by end date
- `page` (integer)
- `limit` (integer)

**Response:**
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "valid_from": "2026-01-01",
      "valid_to": "2030-12-31",
      "approved_harvest_limit": "5000.00",
      "description": "5-year plan",
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-01T00:00:00Z"
    }
  ]
}
```

---

#### Create Operational Plan
```
POST /api/forest/operational-plans/
```

**Permission:** CommitteeOfficer required

**Request Body:**
```json
{
  "valid_from": "2026-01-01",
  "valid_to": "2030-12-31",
  "approved_harvest_limit": "5000.00",
  "description": "5-year operational plan"
}
```

---

#### Retrieve Operational Plan
```
GET /api/forest/operational-plans/{id}/
```

---

#### Update Operational Plan
```
PUT /api/forest/operational-plans/{id}/
PATCH /api/forest/operational-plans/{id}/
```

**Permission:** CommitteeOfficer required

---

#### Delete Operational Plan
```
DELETE /api/forest/operational-plans/{id}/
```

**Permission:** CommitteeOfficer required

---

### Tree Count Register

#### List Tree Count Records
```
GET /api/forest/tree-counts/
```

**Query Parameters:**
- `block` (integer) - Filter by block ID
- `operational_plan` (integer) - Filter by operational plan ID
- `species` (integer) - Filter by species ID
- `tree_class` (string) - Filter by tree class (i, ii, iii)
- `is_harvestable` (boolean) - Filter by harvestable status
- `is_active` (boolean) - Filter by active status
- `plot_number` (integer) - Filter by plot number
- `search` (string) - Search in block name, species name, notes
- `ordering` (string) - Sort by: plot_number, tree_number, girth_cm, height_m, total_volume_cubic_m, created_at
- `page` (integer)
- `limit` (integer)

**Response:**
```json
{
  "count": 150,
  "results": [
    {
      "id": 1,
      "block": 1,
      "block_name": "Block A",
      "operational_plan": 1,
      "species": 1,
      "species_name": "Sal",
      "plot_number": 1,
      "tree_number": 5,
      "girth_cm": "120.5",
      "height_m": "25.3",
      "tree_class": "i",
      "tree_class_display": "I",
      "basal_area_sqm": "1.1547",
      "stem_volume_cubic_m": "13.0905",
      "r_factor": "0.00",
      "branch_volume_cubic_m": "0.0000",
      "total_volume_cubic_m": "13.0905",
      "r_less_than_10": "0.00",
      "volume_less_than_10_cubic_m": "0.000",
      "gross_volume_cubic_m": "12.4359",
      "net_volume_cubic_m": "9.9487",
      "fuelwood_volume_cubic_m": "4.3526",
      "survey_date": "2026-01-15",
      "is_harvestable": true,
      "is_active": true,
      "notes": "Healthy tree",
      "created_at": "2026-01-15T10:30:00Z",
      "updated_at": "2026-01-15T10:30:00Z"
    }
  ]
}
```

---

#### Create Tree Count Record
```
POST /api/forest/tree-counts/
```

**Permission:** CommitteeOfficer required

**Request Body:**
```json
{
  "block": 1,
  "operational_plan": 1,
  "species": 1,
  "plot_number": 1,
  "tree_number": 5,
  "girth_cm": "120.5",
  "height_m": "25.3",
  "tree_class": "i",
  "survey_date": "2026-01-15",
  "is_harvestable": true,
  "notes": "Healthy tree, good condition"
}
```

**Response (201 Created):** Full tree record with auto-calculated volumes

---

#### Retrieve Tree Count Record
```
GET /api/forest/tree-counts/{id}/
```

---

#### Update Tree Count Record
```
PUT /api/forest/tree-counts/{id}/
PATCH /api/forest/tree-counts/{id}/
```

**Permission:** CommitteeOfficer required

**Note:** Updating girth, height, or tree_class will recalculate all volume fields

---

#### Delete Tree Count Record
```
DELETE /api/forest/tree-counts/{id}/
```

**Permission:** CommitteeOfficer required

---

#### Plot Summary
```
GET /api/forest/tree-counts/plot-summary/?block_id={block_id}&section_id={section_id}&plot_number={plot_number}
```

**Query Parameters (all required):**
- `block_id` (integer) - Forest block ID
- `section_id` (integer) - Section ID
- `plot_number` (integer) - Plot number

**Response:**
```json
{
  "block_id": 1,
  "section_id": 1,
  "plot_number": 1,
  "total_trees": 45,
  "total_volume": "500.00",
  "total_net_volume": "400.00",
  "total_fuelwood": "150.00",
  "species_count": 3,
  "average_height": "22.50",
  "average_girth": "110.00",
  "trees": [...]
}
```

---

#### Section Summary
```
GET /api/forest/tree-counts/section-summary/?block_id={block_id}&section_id={section_id}
```

**Query Parameters (all required):**
- `block_id` (integer)
- `section_id` (integer)

**Response:**
```json
{
  "block_id": 1,
  "section_id": 1,
  "total_trees": 450,
  "total_plots": 10,
  "total_volume": "5000.00",
  "total_net_volume": "4000.00",
  "total_fuelwood": "1500.00",
  "species_count": 5,
  "average_height": "23.00",
  "average_girth": "115.00"
}
```

---

#### Block Summary
```
GET /api/forest/tree-counts/block-summary/?block_id={block_id}&operational_plan_id={operational_plan_id}
```

**Query Parameters:**
- `block_id` (integer, required)
- `operational_plan_id` (integer, optional)

**Response:**
```json
{
  "block_id": 1,
  "block_name": "Block A",
  "total_trees": 2500,
  "total_sections": 5,
  "total_plots": 50,
  "total_volume": "30000.00",
  "total_net_volume": "24000.00",
  "total_fuelwood": "9000.00",
  "species_count": 8,
  "species_list": ["Sal", "Pine", "Oak", ...],
  "average_height": "24.00",
  "average_girth": "120.00",
  "class_i_count": 1000,
  "class_ii_count": 1000,
  "class_iii_count": 500,
  "harvestable_count": 2300,
  "non_harvestable_count": 200
}
```

---

#### Species Distribution
```
GET /api/forest/tree-counts/species-distribution/?block_id={block_id}&operational_plan_id={operational_plan_id}
```

**Query Parameters:**
- `block_id` (integer, required)
- `operational_plan_id` (integer, optional)

**Response:**
```json
[
  {
    "species_id": 1,
    "species_name": "Sal",
    "total_trees": 1500,
    "total_volume": "18000.00",
    "sections": {
      "1": 300,
      "2": 250,
      "3": 200,
      ...
    }
  },
  {
    "species_id": 2,
    "species_name": "Pine",
    "total_trees": 800,
    "total_volume": "9600.00",
    "sections": {...}
  }
]
```

---

#### Bulk Create Tree Records
```
POST /api/forest/tree-counts/bulk-create/
```

**Permission:** CommitteeOfficer required

**Request Body:** Array of up to 100 records
```json
[
  {
    "block": 1,
    "operational_plan": 1,
    "species": 1,
    "plot_number": 1,
    "tree_number": 1,
    "girth_cm": "100.0",
    "height_m": "20.0",
    "tree_class": "i"
  },
  {
    "block": 1,
    "operational_plan": 1,
    "species": 1,
    "plot_number": 1,
    "tree_number": 2,
    "girth_cm": "120.0",
    "height_m": "25.0",
    "tree_class": "ii"
  }
]
```

**Response (207 Multi-Status):**
```json
{
  "created": [
    {
      "index": 0,
      "id": 100,
      "block": "Block A",
      "plot": 1,
      "tree_number": 1,
      "species": "Sal"
    }
  ],
  "errors": [
    {
      "index": 1,
      "errors": {"girth_cm": ["Girth must be greater than 0."]}
    }
  ],
  "total_processed": 2,
  "total_created": 1,
  "total_errors": 1
}
```

---

#### Get Trees by Plot
```
GET /api/forest/tree-counts/by-plot/?block_id={block_id}&section_id={section_id}&plot_number={plot_number}
```

**Query Parameters (all required):**
- `block_id` (integer)
- `section_id` (integer)
- `plot_number` (integer)

**Response:** Array of tree records for the specified plot

---

### Tree Count History

#### List History Records
```
GET /api/forest/tree-count-history/
```

**Query Parameters:**
- `record` (integer) - Filter by tree record ID
- `change_date` (date) - Filter by change date
- `record__block` (integer) - Filter by block ID
- `record__species` (integer) - Filter by species ID
- `ordering` (string) - Sort by: change_date
- `page` (integer)
- `limit` (integer)

**Response:**
```json
{
  "count": 50,
  "results": [
    {
      "id": 1,
      "record": 5,
      "record_details": {
        "species": "Sal",
        "block": "Block A",
        "plot": "1",
        "tree_number": 5
      },
      "change_amount": 10,
      "reference_harvest": 1,
      "change_date": "2026-02-20",
      "note": "Harvested in batch",
      "created_at": "2026-02-20T14:30:00Z"
    }
  ]
}
```

---

#### Create History Record
```
POST /api/forest/tree-count-history/
```

**Permission:** CommitteeOfficer required

**Request Body:**
```json
{
  "record": 5,
  "change_amount": 10,
  "reference_harvest": 1,
  "change_date": "2026-02-20",
  "note": "Harvested in batch"
}
```

---

#### Retrieve History Record
```
GET /api/forest/tree-count-history/{id}/
```

---

#### Update History Record
```
PUT /api/forest/tree-count-history/{id}/
PATCH /api/forest/tree-count-history/{id}/
```

**Permission:** CommitteeOfficer required

---

#### Delete History Record
```
DELETE /api/forest/tree-count-history/{id}/
```

**Permission:** CommitteeOfficer required

---

### Harvest Logs

#### List Harvest Logs
```
GET /api/forest/harvest-logs/
```

**Query Parameters:**
- `tree_record` (integer) - Filter by tree record ID
- `harvest_date` (date) - Filter by harvest date
- `tree_record__block` (integer) - Filter by block ID
- `tree_record__species` (integer) - Filter by species ID
- `ordering` (string) - Sort by: harvest_date
- `page` (integer)
- `limit` (integer)

**Response:**
```json
{
  "count": 100,
  "results": [
    {
      "id": 1,
      "tree_record": 5,
      "tree_details": {
        "species": "Sal",
        "block": "Block A",
        "plot": "1",
        "tree_number": 5,
        "total_volume": "13.0905",
        "net_volume": "9.9487"
      },
      "harvest_date": "2026-02-20",
      "harvest_quantity_cubic_m": "9.95",
      "reference_harvest_request": 1,
      "notes": "Successfully harvested",
      "created_at": "2026-02-20T14:30:00Z",
      "updated_at": "2026-02-20T14:30:00Z"
    }
  ]
}
```

---

#### Create Harvest Log
```
POST /api/forest/harvest-logs/
```

**Permission:** CommitteeOfficer required

**Request Body:**
```json
{
  "tree_record": 5,
  "harvest_date": "2026-02-20",
  "harvest_quantity_cubic_m": "9.95",
  "reference_harvest_request": 1,
  "notes": "Successfully harvested"
}
```

---

#### Retrieve Harvest Log
```
GET /api/forest/harvest-logs/{id}/
```

---

#### Update Harvest Log
```
PUT /api/forest/harvest-logs/{id}/
PATCH /api/forest/harvest-logs/{id}/
```

**Permission:** CommitteeOfficer required

---

#### Delete Harvest Log
```
DELETE /api/forest/harvest-logs/{id}/
```

**Permission:** CommitteeOfficer required

---

### Pole Count Register

#### List Pole Count Records
```
GET /api/forest/pole-counts/
```

**Query Parameters:** Same as Tree Count Register

**Response:** Same structure as TreeCountRegister

---

#### Create Pole Count Record
```
POST /api/forest/pole-counts/
```

**Permission:** CommitteeOfficer required

**Request Body:** Same as TreeCountRegister

---

#### Retrieve Pole Count Record
```
GET /api/forest/pole-counts/{id}/
```

---

#### Update Pole Count Record
```
PUT /api/forest/pole-counts/{id}/
PATCH /api/forest/pole-counts/{id}/
```

**Permission:** CommitteeOfficer required

---

#### Delete Pole Count Record
```
DELETE /api/forest/pole-counts/{id}/
```

**Permission:** CommitteeOfficer required

---

### Timber Collection

#### List Timber Collections
```
GET /api/forest/timber-collection/
```

**Query Parameters:**
- `block` (integer) - Filter by block ID
- `species` (integer) - Filter by species ID
- `search` (string) - Search in block name, species name
- `ordering` (string) - Sort by: block__block_name, species__species_name, wood_volume, firewood
- `page` (integer)
- `limit` (integer)

**Response:**
```json
{
  "count": 50,
  "results": [
    {
      "id": 1,
      "block": 1,
      "block_name": "Block A",
      "species": 1,
      "species_name": "Sal",
      "wood_volume": "1500.75",
      "firewood": "400.25",
      "created_at": "2026-01-15T10:30:00Z",
      "updated_at": "2026-01-15T10:30:00Z"
    }
  ]
}
```

---

#### Create Timber Collection
```
POST /api/forest/timber-collection/
```

**Permission:** CommitteeOfficer required

**Request Body:**
```json
{
  "block": 1,
  "species": 1,
  "wood_volume": "1500.75",
  "firewood": "400.25"
}
```

**Response (201 Created):** Full timber collection record

---

#### Retrieve Timber Collection
```
GET /api/forest/timber-collection/{id}/
```

---

#### Update Timber Collection
```
PUT /api/forest/timber-collection/{id}/
PATCH /api/forest/timber-collection/{id}/
```

**Permission:** CommitteeOfficer required

---

#### Delete Timber Collection
```
DELETE /api/forest/timber-collection/{id}/
```

**Permission:** CommitteeOfficer required

---

#### Block Summary
```
GET /api/forest/timber-collection/block-summary/?block_id={block_id}
```

**Query Parameters:**
- `block_id` (integer, required)

**Response:**
```json
{
  "block_id": 1,
  "block_name": "Block A",
  "total_species": 5,
  "total_wood_volume": "7500.00",
  "total_firewood": "2000.00",
  "species": [
    {
      "species_id": 1,
      "species_name": "Sal",
      "wood_volume": "1500.75",
      "firewood": "400.25"
    }
  ]
}
```

---

#### Species Summary
```
GET /api/forest/timber-collection/species-summary/?species_id={species_id}
```

**Query Parameters:**
- `species_id` (integer, required)

**Response:**
```json
{
  "species_id": 1,
  "species_name": "Sal",
  "total_blocks": 3,
  "total_wood_volume": "4500.00",
  "total_firewood": "1200.00",
  "blocks": [
    {
      "block_id": 1,
      "block_name": "Block A",
      "wood_volume": "1500.75",
      "firewood": "400.25"
    }
  ]
}
```

---

#### Total Summary
```
GET /api/forest/timber-collection/total-summary/
```

**Response:**
```json
{
  "total_blocks": 5,
  "total_species": 8,
  "total_records": 50,
  "total_wood_volume": "20000.00",
  "total_firewood": "5000.00"
}
```

---

#### Bulk Create Timber Collections
```
POST /api/forest/timber-collection/bulk-create/
```

**Permission:** CommitteeOfficer required

**Request Body:** Array of up to 100 records
```json
[
  {
    "block": 1,
    "species": 1,
    "wood_volume": "1500.00",
    "firewood": "400.00"
  },
  {
    "block": 1,
    "species": 2,
    "wood_volume": "800.00",
    "firewood": "200.00"
  }
]
```

**Response (207 Multi-Status):** Same as TreeCountRegister bulk-create

---

## Error Handling

### Standard Error Responses

#### 400 Bad Request
```json
{
  "error": "Invalid query parameters",
  "details": "block_id is required"
}
```

#### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

#### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

#### 404 Not Found
```json
{
  "detail": "Not found."
}
```

#### 409 Conflict (Duplicate)
```json
{
  "detail": "A timber collection record already exists for this block and species."
}
```

#### 422 Unprocessable Entity
```json
{
  "girth_cm": ["Girth must be greater than 0.", "Girth cannot exceed 500 cm."],
  "height_m": ["Height must be greater than 0."],
  "tree_class": ["Tree class must be 'i', 'ii', or 'iii'."]
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Internal server error occurred."
}
```

---

## Common Patterns

### Pagination
All list endpoints support pagination:

```
GET /api/forest/blocks/?page=2&limit=50
```

**Response Structure:**
```json
{
  "count": 100,
  "next": "http://api.example.com/api/forest/blocks/?page=3&limit=50",
  "previous": "http://api.example.com/api/forest/blocks/?page=1&limit=50",
  "results": [...]
}
```

---

### Filtering
Endpoints support multiple filter fields:

```
GET /api/forest/tree-counts/?block=1&species=1&tree_class=i&is_harvestable=true
```

---

### Searching
Text search across relevant fields:

```
GET /api/forest/tree-counts/?search=sal
GET /api/forest/species/?search=robusta
```

---

### Sorting
Use the `ordering` parameter:

```
GET /api/forest/tree-counts/?ordering=total_volume_cubic_m
GET /api/forest/tree-counts/?ordering=-total_volume_cubic_m  # Descending
```

---

### Bulk Operations
For bulk create operations:
- Maximum 100 records per request
- Returns 207 Multi-Status with created and error arrays
- Partial success is allowed

```
POST /api/forest/tree-counts/bulk-create/
```

---

### Authentication Header
Include JWT token in all requests:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

### Response Headers
All responses include standard headers:

```
Content-Type: application/json
Cache-Control: no-cache
X-Content-Type-Options: nosniff
```

---

## Integration Notes for Frontend

### Volume Calculations
Tree volumes are automatically calculated on the server:
- **Basal Area** = π × (DBH/2)² where DBH = girth/π
- **Stem Volume** = Basal Area × Height × Form Factor (0.45)
- **R Factor** varies by tree class:
  - Class I: 0.00
  - Class II: 0.15
  - Class III: 0.30
- **Branch Volume** = Stem Volume × R Factor
- **Total Volume** = Stem + Branch
- **Gross Volume** = Total × 0.95 (5% bark loss)
- **Net Volume** = Gross × 0.80 (20% waste)
- **Fuelwood** = Gross × 0.35

### Date Formats
- Use ISO 8601 format for dates: `YYYY-MM-DD`
- Use ISO 8601 format for datetimes: `YYYY-MM-DDTHH:MM:SSZ`

### Decimal Precision
- Volume fields: 3 decimal places (cubic meters)
- Girth measurements: 1 decimal place (cm)
- Height measurements: 1 decimal place (meters)
- Basal area: 4 decimal places (square meters)

### Common Query Patterns

**Get all harvestable trees in a block:**
```
GET /api/forest/tree-counts/?block=1&is_harvestable=true
```

**Get trees by species:**
```
GET /api/forest/tree-counts/?species=1&ordering=-total_volume_cubic_m
```

**Get summary for a specific plot:**
```
GET /api/forest/tree-counts/plot-summary/?block_id=1&section_id=1&plot_number=5
```

**Track harvest changes:**
```
GET /api/forest/tree-count-history/?record__block=1&ordering=-change_date
```

---

## Rate Limiting
- No specific rate limits documented
- Contact API administrator for usage policies

---

## Support & Documentation
For additional support:
- Check the API_STRUCTURE.md for architectural overview
- Review individual model docstrings in the codebase
- Contact the Forest App development team
