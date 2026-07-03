# Tree Survey Forms API Documentation

## Overview

The Tree Survey Forms app provides functionality to create, manage, and export tree survey and wood collection forms (अनुसूची-७) in printable PDF format. It integrates with the forest inventory system to track wood collection and harvesting activities.

## Features

- **Survey Form Management**: Create and manage tree survey forms with complete metadata
- **Tree Item Tracking**: Record individual tree measurements and volumes within forms
- **PDF Export**: Generate professional printable PDFs of survey forms
- **Bulk Export**: Export multiple forms as a single PDF document
- **Search & Filter**: Filter forms by block, operational plan, and date ranges
- **Admin Interface**: User-friendly Django admin for form management

## Models

### TreeSurveyForm

Main model for survey forms.

**Fields:**
- `form_number` (CharField): Unique form identifier (पूर्जी क्र.स.)
- `survey_date` (DateField): Date of survey/measurement
- `block` (ForeignKey): Reference to ForestBlock
- `operational_plan` (ForeignKey): Reference to OperationalPlan (optional)
- `district` (CharField): District name (जिल्ला)
- `municipality` (CharField): Municipality/VDC name (गाउँपालिका / नगरपालिका)
- `ward_number` (PositiveIntegerField): Ward number
- `plot_number` (PositiveIntegerField): Plot identification number
- `forest_category` (CharField): Forest category/type
- `community_representative` (CharField): Name of community representative
- `community_representative_sign_date` (DateField): Representative signature date
- `forest_officer` (CharField): Name of forest officer
- `forest_officer_sign_date` (DateField): Forest officer signature date
- `notes` (TextField): Additional remarks

**Methods:**
- `get_total_volume()`: Calculate total wood volume from all tree items
- `get_total_fuelwood()`: Calculate total fuelwood volume from all tree items

### TreeSurveyFormItem

Individual tree/wood entry within a survey form.

**Fields:**
- `survey_form` (ForeignKey): Reference to TreeSurveyForm
- `serial_number` (PositiveIntegerField): Item sequence number (क्र.स.)
- `species` (ForeignKey): Reference to Species
- `girth_cm` (DecimalField): Girth measurement in centimeters (गोलाई न.)
- `height_m` (DecimalField): Height measurement in meters (लाइड)
- `volume_cubic_m` (DecimalField): Calculated volume in cubic meters (आयतन)
- `fuelwood_volume_cubic_m` (DecimalField): Fuelwood volume in cubic meters (छोटिकरन)
- `wood_type` (CharField): Type of wood (काठ/दाउरा/अन्य)
- `remarks` (TextField): Additional notes

## API Endpoints

### Survey Forms

#### List Survey Forms
```
GET /api/v1/forms/survey-forms/
```

**Query Parameters:**
- `block`: Filter by block ID
- `operational_plan`: Filter by operational plan ID
- `survey_date`: Filter by survey date
- `search`: Search by form_number, district, or municipality
- `ordering`: Sort by -survey_date or form_number

**Response:**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "form_number": "FORM-2024-001",
      "survey_date": "2024-07-01",
      "block": 1,
      "block_name": "Main Forest Block",
      "operational_plan": 1,
      "district": "काठमाडौं",
      "municipality": "नुवाकोट नगरपालिका",
      "ward_number": 1,
      "plot_number": 101,
      "forest_category": "Community Forest",
      "community_representative": "राज कुमार शर्मा",
      "community_representative_sign_date": "2024-07-01",
      "forest_officer": "कृष्ण प्रसाद गुप्ता",
      "forest_officer_sign_date": "2024-07-02",
      "tree_items": [...],
      "total_volume": 45.250,
      "total_fuelwood": 12.500,
      "notes": "Survey completed successfully",
      "created_at": "2024-07-01T10:30:00Z",
      "updated_at": "2024-07-01T10:30:00Z"
    }
  ]
}
```

#### Create Survey Form
```
POST /api/v1/forms/survey-forms/
```

**Request Body:**
```json
{
  "form_number": "FORM-2024-002",
  "survey_date": "2024-07-02",
  "block": 1,
  "operational_plan": 1,
  "district": "काठमाडौं",
  "municipality": "नुवाकोट नगरपालिका",
  "ward_number": 2,
  "plot_number": 102,
  "forest_category": "Community Forest",
  "community_representative": "राज कुमार शर्मा",
  "community_representative_sign_date": "2024-07-02",
  "forest_officer": "कृष्ण प्रसाद गुप्ता",
  "forest_officer_sign_date": "2024-07-02",
  "notes": "Form for plot 102"
}
```

#### Retrieve Survey Form
```
GET /api/v1/forms/survey-forms/{id}/
```

#### Update Survey Form
```
PUT /api/v1/forms/survey-forms/{id}/
PATCH /api/v1/forms/survey-forms/{id}/
```

#### Delete Survey Form
```
DELETE /api/v1/forms/survey-forms/{id}/
```

#### Export Single Form as PDF
```
GET /api/v1/forms/survey-forms/{id}/pdf/
```

**Response:** PDF file download

#### Export Multiple Forms as PDF
```
POST /api/v1/forms/survey-forms/bulk-pdf/
```

**Request Body:**
```json
{
  "form_ids": [1, 2, 3]
}
```

**Response:** PDF file download

### Survey Form Items

#### List Form Items
```
GET /api/v1/forms/survey-form-items/
```

**Query Parameters:**
- `survey_form`: Filter by survey form ID
- `species`: Filter by species ID
- `search`: Search by species name

**Response:**
```json
{
  "count": 25,
  "results": [
    {
      "id": 1,
      "serial_number": 1,
      "species": 1,
      "species_name": "साल (Sal)",
      "girth_cm": "125.5",
      "height_m": "18.5",
      "volume_cubic_m": "2.450",
      "fuelwood_volume_cubic_m": "0.500",
      "wood_type": "timber",
      "remarks": "Good quality timber",
      "created_at": "2024-07-01T10:30:00Z",
      "updated_at": "2024-07-01T10:30:00Z"
    }
  ]
}
```

#### Create Form Item
```
POST /api/v1/forms/survey-form-items/
```

**Request Body:**
```json
{
  "survey_form": 1,
  "serial_number": 1,
  "species": 1,
  "girth_cm": "125.5",
  "height_m": "18.5",
  "volume_cubic_m": "2.450",
  "fuelwood_volume_cubic_m": "0.500",
  "wood_type": "timber",
  "remarks": "Good quality timber"
}
```

#### Update Form Item
```
PUT /api/v1/forms/survey-form-items/{id}/
PATCH /api/v1/forms/survey-form-items/{id}/
```

#### Delete Form Item
```
DELETE /api/v1/forms/survey-form-items/{id}/
```

## Usage Examples

### Python/Django ORM

```python
from apps.forms.models import TreeSurveyForm, TreeSurveyFormItem
from apps.forest.models import ForestBlock, Species

# Create a new survey form
block = ForestBlock.objects.first()
form = TreeSurveyForm.objects.create(
    form_number="FORM-2024-003",
    survey_date="2024-07-03",
    block=block,
    district="काठमाडौं",
    municipality="नुवाकोट नगरपालिका",
    ward_number=3,
    plot_number=103,
    forest_category="Community Forest",
    community_representative="राज कुमार शर्मा",
    forest_officer="कृष्ण प्रसाद गुप्ता",
)

# Add tree items
species = Species.objects.filter(species_name__icontains="sal").first()
item = TreeSurveyFormItem.objects.create(
    survey_form=form,
    serial_number=1,
    species=species,
    girth_cm=125.5,
    height_m=18.5,
    volume_cubic_m=2.450,
    fuelwood_volume_cubic_m=0.500,
    wood_type="timber",
)

# Get totals
print(f"Total volume: {form.get_total_volume()} m³")
print(f"Total fuelwood: {form.get_total_fuelwood()} m³")
```

### JavaScript/Fetch API

```javascript
// Get all survey forms
async function getSurveyForms() {
  const response = await fetch('/api/v1/forms/survey-forms/');
  const data = await response.json();
  return data.results;
}

// Create a new survey form
async function createSurveyForm(formData) {
  const response = await fetch('/api/v1/forms/survey-forms/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Token ${authToken}`
    },
    body: JSON.stringify(formData)
  });
  return response.json();
}

// Export form as PDF
async function exportFormPDF(formId) {
  window.location.href = `/api/v1/forms/survey-forms/${formId}/pdf/`;
}

// Export multiple forms as PDF
async function exportMultiplePDFs(formIds) {
  const response = await fetch('/api/v1/forms/survey-forms/bulk-pdf/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Token ${authToken}`
    },
    body: JSON.stringify({ form_ids: formIds })
  });
  
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `survey_forms_${new Date().toISOString().split('T')[0]}.pdf`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
}
```

## PDF Format

The exported PDF includes:

1. **Title**: अनुसूची-७ प्लटबाट प्राप्तकोसिम काठ, बाउरा खुवाई गरेर विक्रेचलानी पूर्जी
2. **Form Header**: Block, district, municipality, ward, plot information
3. **Tree Items Table**: Serial number, species, girth, height, volumes
4. **Totals Row**: Total volume and fuelwood calculations
5. **Signature Section**: Fields for community representative, forest officer with dates

## Authentication

All API endpoints require authentication. Include your authentication token in the request header:

```
Authorization: Token YOUR_AUTH_TOKEN
```

## Error Handling

**400 Bad Request**: Invalid input data
```json
{
  "field_name": ["Error message"]
}
```

**404 Not Found**: Resource not found
```json
{
  "detail": "Not found."
}
```

**500 Internal Server Error**: Server error
```json
{
  "detail": "Internal server error"
}
```

## Permissions

- **List/Retrieve**: Authenticated users
- **Create/Update/Delete**: Authenticated users with appropriate permissions
- **Export PDF**: Authenticated users

## Performance Considerations

- Use `prefetch_related()` for related species and survey forms
- Filter results before exporting large PDF batches
- Consider pagination for large result sets

## Future Enhancements

- Email form submissions directly
- Digital signature support
- Template customization
- Multilingual form support (Nepali/English)
- GPS coordinates for plots
- Photo attachments
- Form version history
- Export to Excel format
