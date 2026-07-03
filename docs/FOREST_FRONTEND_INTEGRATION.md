# Forest App - Frontend Integration Guide

**Last Updated:** July 2026

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [API Base URLs](#api-base-urls)
3. [Authentication Setup](#authentication-setup)
4. [Common Frontend Workflows](#common-frontend-workflows)
5. [Data Types & Validation Rules](#data-types--validation-rules)
6. [Request/Response Examples](#requestresponse-examples)
7. [Error Handling](#error-handling)
8. [Performance Optimization](#performance-optimization)

---

## Quick Start

### Essential Endpoints for Frontend

| Feature | Endpoints |
|---------|-----------|
| **List Blocks** | `GET /api/forest/blocks/` |
| **List Species** | `GET /api/forest/species/` |
| **List Trees** | `GET /api/forest/tree-counts/` |
| **Create Tree** | `POST /api/forest/tree-counts/` |
| **Get Block Summary** | `GET /api/forest/tree-counts/block-summary/` |
| **Harvest Logs** | `GET /api/forest/harvest-logs/` |
| **Timber Collections** | `GET /api/forest/timber-collection/` |

---

## API Base URLs

```
Development:  http://localhost:8000/api/forest/
Staging:      https://staging.api.example.com/api/forest/
Production:   https://api.example.com/api/forest/
```

---

## Authentication Setup

### 1. Get JWT Token

```
POST /api/token/
```

**Request:**
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 2. Use Token in Requests

```javascript
// JavaScript/Fetch
const headers = {
  'Authorization': `Bearer ${accessToken}`,
  'Content-Type': 'application/json'
};

fetch('/api/forest/blocks/', {
  method: 'GET',
  headers: headers
})
```

```javascript
// Axios
const instance = axios.create({
  baseURL: 'http://localhost:8000/api/forest/',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  }
});
```

### 3. Token Refresh

When access token expires:

```
POST /api/token/refresh/
```

**Request:**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

## Common Frontend Workflows

### Workflow 1: Display Forest Block Dashboard

**Goal:** Show overview of all forest blocks with key statistics

```javascript
// 1. Fetch all blocks
const blocksResponse = await fetch('/api/forest/blocks/');
const blocks = await blocksResponse.json();

// 2. For each block, fetch summary
const blockSummaries = await Promise.all(
  blocks.results.map(block =>
    fetch(`/api/forest/tree-counts/block-summary/?block_id=${block.id}`)
      .then(r => r.json())
  )
);

// 3. Display data
displayBlockDashboard(blockSummaries);
```

**Response Structure:**
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "block_name": "Block A",
      "area_hectares": "150.50"
    },
    {
      "id": 2,
      "block_name": "Block B",
      "area_hectares": "200.00"
    }
  ]
}
```

---

### Workflow 2: Add New Tree to Inventory

**Goal:** Create a new tree record in the system

```javascript
// Step 1: Get required data (blocks, species, operational plans)
const blocks = await fetch('/api/forest/blocks/').then(r => r.json());
const species = await fetch('/api/forest/species/').then(r => r.json());
const plans = await fetch('/api/forest/operational-plans/').then(r => r.json());

// Step 2: Display form with dropdowns

// Step 3: Submit tree data
const treeData = {
  block: formData.blockId,
  operational_plan: formData.planId,
  species: formData.speciesId,
  plot_number: parseInt(formData.plotNumber),
  tree_number: parseInt(formData.treeNumber),
  girth_cm: parseFloat(formData.girthCm),
  height_m: parseFloat(formData.heightM),
  tree_class: formData.treeClass,
  survey_date: formData.surveyDate,
  is_harvestable: formData.isHarvestable,
  notes: formData.notes
};

const response = await fetch('/api/forest/tree-counts/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(treeData)
});

const createdTree = await response.json();
console.log('Tree created with ID:', createdTree.id);
```

**Validation Rules (Frontend):**
```javascript
const validations = {
  girth_cm: {
    required: true,
    min: 0,
    max: 500,
    pattern: /^\d+(\.\d{1})?$/,
    message: "Girth must be between 0 and 500 cm with up to 1 decimal place"
  },
  height_m: {
    required: true,
    min: 0,
    max: 100,
    pattern: /^\d+(\.\d{1})?$/,
    message: "Height must be between 0 and 100 meters with up to 1 decimal place"
  },
  tree_class: {
    required: true,
    values: ["i", "ii", "iii"],
    message: "Tree class must be I, II, or III"
  },
  plot_number: {
    required: true,
    min: 1,
    message: "Plot number must be greater than 0"
  },
  tree_number: {
    required: true,
    min: 1,
    message: "Tree number must be greater than 0"
  }
};
```

---

### Workflow 3: Filter Trees by Criteria

**Goal:** Search for trees matching specific criteria

```javascript
// Get trees in Block A that are harvestable
const filters = {
  block: 1,
  is_harvestable: true,
  tree_class: "i",
  ordering: "-total_volume_cubic_m"
};

const queryString = new URLSearchParams(filters).toString();
const response = await fetch(`/api/forest/tree-counts/?${queryString}`);
const trees = await response.json();

// Display results grouped by species
const bySpecies = {};
trees.results.forEach(tree => {
  if (!bySpecies[tree.species_name]) {
    bySpecies[tree.species_name] = [];
  }
  bySpecies[tree.species_name].push(tree);
});
```

---

### Workflow 4: Get Plot Summary

**Goal:** Display all trees in a specific plot with statistics

```javascript
// Fetch plot summary
const plotSummary = await fetch(
  '/api/forest/tree-counts/plot-summary/' +
  '?block_id=1&section_id=1&plot_number=5'
).then(r => r.json());

// Display summary info
displayInfo({
  totalTrees: plotSummary.total_trees,
  averageGirth: plotSummary.average_girth,
  averageHeight: plotSummary.average_height,
  totalVolume: plotSummary.total_volume,
  netVolume: plotSummary.total_net_volume,
  fuelwood: plotSummary.total_fuelwood,
  speciesCount: plotSummary.species_count
});

// Display individual trees
displayTrees(plotSummary.trees);
```

---

### Workflow 5: Harvest Tree and Log

**Goal:** Mark a tree as harvested and log the harvest

```javascript
// Step 1: Create harvest log
const harvestLog = {
  tree_record: treeId,
  harvest_date: new Date().toISOString().split('T')[0],
  harvest_quantity_cubic_m: parseFloat(netVolume),
  reference_harvest_request: harvestRequestId,
  notes: "Harvested successfully"
};

const harvestResponse = await fetch('/api/forest/harvest-logs/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(harvestLog)
});

// Step 2: Record history
const history = {
  record: treeId,
  change_amount: 1,
  reference_harvest: harvestRequestId,
  change_date: new Date().toISOString().split('T')[0],
  note: "Logged in batch harvest"
};

await fetch('/api/forest/tree-count-history/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(history)
});
```

---

### Workflow 6: Bulk Import Trees

**Goal:** Import multiple tree records at once

```javascript
// Prepare data
const treesToImport = [
  {
    block: 1,
    operational_plan: 1,
    species: 1,
    plot_number: 1,
    tree_number: 1,
    girth_cm: 100.5,
    height_m: 20.0,
    tree_class: "i"
  },
  {
    block: 1,
    operational_plan: 1,
    species: 2,
    plot_number: 1,
    tree_number: 2,
    girth_cm: 120.0,
    height_m: 25.0,
    tree_class: "ii"
  }
  // ... more trees
];

// Submit bulk create
const response = await fetch('/api/forest/tree-counts/bulk-create/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(treesToImport)
});

const result = await response.json();

// Handle results
console.log(`Created: ${result.total_created} trees`);
console.log(`Errors: ${result.total_errors} trees`);

result.errors.forEach(error => {
  console.error(`Row ${error.index}: ${JSON.stringify(error.errors)}`);
});
```

---

### Workflow 7: Generate Species Distribution Report

**Goal:** Get species breakdown for visualization

```javascript
// Fetch species distribution
const distribution = await fetch(
  '/api/forest/tree-counts/species-distribution/?block_id=1'
).then(r => r.json());

// Format for chart
const chartData = distribution.map(species => ({
  name: species.species_name,
  trees: species.total_trees,
  volume: parseFloat(species.total_volume),
  sections: species.sections
}));

// Sort by volume
chartData.sort((a, b) => b.volume - a.volume);

// Display chart
displayPieChart(chartData);
```

---

## Data Types & Validation Rules

### Numeric Fields

#### Girth (cm)
- **Type:** Decimal (up to 6 digits, 1 decimal place)
- **Range:** > 0 and ≤ 500
- **Format:** `XXX.X`
- **Example:** `120.5`

#### Height (m)
- **Type:** Decimal (up to 5 digits, 1 decimal place)
- **Range:** > 0 and ≤ 100
- **Format:** `XX.X`
- **Example:** `25.3`

#### Volume (cubic meters)
- **Type:** Decimal (up to 10 digits, 3 decimal places)
- **Format:** `XXXXXXX.XXX`
- **Example:** `13.090`, `9.949`

#### Area (hectares)
- **Type:** Decimal (up to 10 digits, 2 decimal places)
- **Range:** ≥ 0
- **Format:** `XXXXXXXX.XX`
- **Example:** `150.50`

### String Fields

#### Block Name
- **Type:** String
- **Max Length:** 255 characters
- **Required:** Yes
- **Example:** `"Block A"`, `"North Forest Section"`

#### Species Name
- **Type:** String
- **Max Length:** 255 characters
- **Unique:** Yes
- **Required:** Yes
- **Example:** `"Sal"`, `"Pine"`, `"Oak"`

#### Scientific Name
- **Type:** String
- **Max Length:** 255 characters
- **Required:** No
- **Example:** `"Shorea robusta"`

#### Local Name
- **Type:** String
- **Max Length:** 255 characters
- **Required:** No
- **Example:** `"सालको रुख"`

#### Tree Class
- **Type:** Choice String
- **Valid Values:** `"i"`, `"ii"`, `"iii"`
- **Display Values:** `"I"`, `"II"`, `"III"`
- **Required:** Yes

#### Notes
- **Type:** Text
- **Max Length:** Unlimited
- **Required:** No
- **Example:** `"Healthy tree, suitable for harvest"`

### Date/Time Fields

#### Date (ISO 8601)
- **Format:** `YYYY-MM-DD`
- **Example:** `"2026-01-15"`

#### DateTime (ISO 8601)
- **Format:** `YYYY-MM-DDTHH:MM:SSZ`
- **Example:** `"2026-01-15T10:30:00Z"`

### Boolean Fields

- **Valid Values:** `true`, `false`
- **JSON Type:** Boolean
- **Example:** `"is_harvestable": true`

---

## Request/Response Examples

### Example 1: Create Single Tree

**Request:**
```javascript
POST /api/forest/tree-counts/
Authorization: Bearer token123
Content-Type: application/json

{
  "block": 1,
  "operational_plan": 1,
  "species": 1,
  "plot_number": 1,
  "tree_number": 5,
  "girth_cm": 120.5,
  "height_m": 25.3,
  "tree_class": "i",
  "survey_date": "2026-01-15",
  "is_harvestable": true,
  "notes": "Healthy tree, good condition"
}
```

**Response (201 Created):**
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

---

### Example 2: Create Forest Block

**Request:**
```javascript
POST /api/forest/blocks/
Authorization: Bearer token123
Content-Type: application/json

{
  "block_name": "Block C",
  "area_hectares": 175.50
}
```

**Response (201 Created):**
```json
{
  "id": 3,
  "block_name": "Block C",
  "area_hectares": "175.50",
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-01-15T10:30:00Z"
}
```

---

### Example 3: Create Species

**Request:**
```javascript
POST /api/forest/species/
Authorization: Bearer token123
Content-Type: application/json

{
  "species_name": "Chir Pine",
  "scientific_name": "Pinus roxburghii",
  "local_name": "चीड"
}
```

**Response (201 Created):**
```json
{
  "id": 3,
  "species_name": "Chir Pine",
  "scientific_name": "Pinus roxburghii",
  "local_name": "चीड",
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-01-15T10:30:00Z"
}
```

---

### Example 4: Create Harvest Log

**Request:**
```javascript
POST /api/forest/harvest-logs/
Authorization: Bearer token123
Content-Type: application/json

{
  "tree_record": 1,
  "harvest_date": "2026-02-20",
  "harvest_quantity_cubic_m": 9.95,
  "reference_harvest_request": 1,
  "notes": "Successfully harvested"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "tree_record": 1,
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

---

### Example 5: Filter Trees

**Request:**
```
GET /api/forest/tree-counts/?block=1&species=1&is_harvestable=true&ordering=-total_volume_cubic_m&limit=10
Authorization: Bearer token123
```

**Response:**
```json
{
  "count": 250,
  "next": "http://api.example.com/api/forest/tree-counts/?block=1&page=2",
  "previous": null,
  "results": [
    {
      "id": 10,
      "block": 1,
      "block_name": "Block A",
      "species": 1,
      "species_name": "Sal",
      "plot_number": 2,
      "tree_number": 15,
      "girth_cm": "150.0",
      "height_m": "30.0",
      "tree_class": "i",
      "tree_class_display": "I",
      "total_volume_cubic_m": "25.5000",
      "net_volume_cubic_m": "20.4000",
      "fuelwood_volume_cubic_m": "8.9280",
      "is_harvestable": true,
      "created_at": "2026-01-10T09:00:00Z"
    }
  ]
}
```

---

### Example 6: Block Summary

**Request:**
```
GET /api/forest/tree-counts/block-summary/?block_id=1
Authorization: Bearer token123
```

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
  "species_list": [
    "Sal",
    "Pine",
    "Oak",
    "Khair",
    "Dhauri",
    "Bahera",
    "Sisoo",
    "Teak"
  ],
  "average_height": 24.0,
  "average_girth": 120.0,
  "class_i_count": 1000,
  "class_ii_count": 1000,
  "class_iii_count": 500,
  "harvestable_count": 2300,
  "non_harvestable_count": 200
}
```

---

## Error Handling

### Common Error Scenarios

#### 1. Validation Error - Invalid Girth

**Request:**
```json
{
  "girth_cm": 600,
  "height_m": 25.3,
  ...
}
```

**Response (422 Unprocessable Entity):**
```json
{
  "girth_cm": ["Girth cannot exceed 500 cm."]
}
```

---

#### 2. Duplicate Record

**Request:**
```json
{
  "block": 1,
  "plot_number": 1,
  "tree_number": 5,
  ...
}
```

**Response (409 Conflict):**
```json
{
  "detail": "A tree record already exists for this block, plot, and tree number."
}
```

---

#### 3. Missing Required Fields

**Request:**
```json
{
  "block": 1,
  "plot_number": 1,
  "girth_cm": 120.5
}
```

**Response (422 Unprocessable Entity):**
```json
{
  "species": ["This field is required."],
  "tree_number": ["This field is required."],
  "height_m": ["This field is required."],
  "tree_class": ["This field is required."]
}
```

---

#### 4. Authentication Error

**Request (missing token):**
```
GET /api/forest/blocks/
```

**Response (401 Unauthorized):**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

#### 5. Permission Error

**Request (non-CommitteeOfficer trying to create):**
```
POST /api/forest/blocks/
Authorization: Bearer user_token
```

**Response (403 Forbidden):**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

#### 6. Not Found

**Request:**
```
GET /api/forest/blocks/999/
```

**Response (404 Not Found):**
```json
{
  "detail": "Not found."
}
```

---

### Frontend Error Handling Pattern

```javascript
async function handleAPIRequest(endpoint, options = {}) {
  try {
    const response = await fetch(endpoint, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    // Handle different status codes
    if (response.status === 401) {
      // Handle token refresh or redirect to login
      refreshToken();
      return;
    }

    if (response.status === 403) {
      showError('You do not have permission for this action');
      return;
    }

    if (response.status === 404) {
      showError('Resource not found');
      return;
    }

    if (response.status === 409) {
      const data = await response.json();
      showError(`Duplicate record: ${data.detail}`);
      return;
    }

    if (response.status === 422) {
      const data = await response.json();
      displayValidationErrors(data);
      return;
    }

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();

  } catch (error) {
    console.error('API Error:', error);
    showError('An error occurred. Please try again.');
  }
}
```

---

## Performance Optimization

### 1. Use Pagination

```javascript
// Good - retrieve only 20 records at a time
fetch('/api/forest/tree-counts/?limit=20&page=1')

// Bad - retrieves all records
fetch('/api/forest/tree-counts/')
```

### 2. Use Filters to Reduce Data

```javascript
// Good - filter server-side
fetch('/api/forest/tree-counts/?block=1&is_harvestable=true')

// Bad - get all and filter client-side
fetch('/api/forest/tree-counts/')
  .then(r => r.json())
  .then(data => data.results.filter(t => t.block === 1 && t.is_harvestable))
```

### 3. Use Summary Endpoints for Statistics

```javascript
// Good - use dedicated endpoint
fetch('/api/forest/tree-counts/block-summary/?block_id=1')

// Bad - get all trees and calculate
fetch('/api/forest/tree-counts/?block=1')
  .then(r => r.json())
  .then(data => calculateSummary(data.results))
```

### 4. Implement Caching

```javascript
const cache = new Map();

async function getCachedData(endpoint, ttl = 5 * 60 * 1000) {
  const cached = cache.get(endpoint);
  
  if (cached && Date.now() - cached.timestamp < ttl) {
    return cached.data;
  }

  const data = await fetch(endpoint).then(r => r.json());
  cache.set(endpoint, { data, timestamp: Date.now() });
  return data;
}
```

### 5. Batch Operations for Bulk Insert

```javascript
// Use bulk-create endpoint instead of individual POSTs
fetch('/api/forest/tree-counts/bulk-create/', {
  method: 'POST',
  body: JSON.stringify(arrayOf100Items)
})
```

### 6. Lazy Load Data

```javascript
// Load block list
const blocks = await fetch('/api/forest/blocks/?limit=20').then(r => r.json());

// Load block details on demand
async function loadBlockDetails(blockId) {
  return fetch(`/api/forest/tree-counts/block-summary/?block_id=${blockId}`)
    .then(r => r.json());
}
```

---

## Helpful Tips

### Convert Tree Class Display

```javascript
const treeClassDisplay = {
  'i': 'Class I',
  'ii': 'Class II',
  'iii': 'Class III'
};

function getTreeClassName(value) {
  return treeClassDisplay[value] || value;
}
```

### Format Volume Numbers

```javascript
function formatVolume(value, decimals = 2) {
  return parseFloat(value).toFixed(decimals) + ' m³';
}

console.log(formatVolume('13.0905', 2)); // "13.09 m³"
```

### Calculate Total Volume from Trees

```javascript
function calculateTotalVolume(trees) {
  return trees.reduce((sum, tree) => {
    return sum + parseFloat(tree.total_volume_cubic_m || 0);
  }, 0);
}
```

### Get All Species from Trees

```javascript
function getUniqueSpecies(trees) {
  const species = new Map();
  trees.forEach(tree => {
    if (!species.has(tree.species_id)) {
      species.set(tree.species_id, tree.species_name);
    }
  });
  return Array.from(species.values());
}
```

---

## Contact & Support

For API issues or questions:
- Backend Team: backend@forestapp.local
- API Documentation: `/api/forest/`
- Status Page: https://status.forestapp.local
