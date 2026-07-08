# Members API Documentation

## Overview

The Members API manages households, individual members, and membership renewals within the Community Forest system. It provides endpoints for CRUD operations, comprehensive household-level statistics with aggregated member data, and renewal tracking. The API is organized around **households as the primary statistical unit**, with member data aggregated within household views.

## Base URL
```
/api/members/
```

## Authentication & Permissions

All endpoints require authentication. Permission classes vary by endpoint:

- **Public Staff**: `IsCommitteeOfficer` - Full access to all endpoints
- **DFO Viewer**: `IsDFOViewer` - Read-only access to member statistics
- **Member Users**: `IsMember` - Limited access to their own member profile
- **Sub-Committee Members**: `IsSubCommitteeMember` - Limited access to their own profile

---

## Core Models

### Household
Represents a household unit with membership and demographic information.

**Attributes:**
- `id` (integer, read-only)
- `household_head_name` (string, max 255) - Name of the household head
- `tole` (string, blank) - Village/locality name
- `citizenship_no` (string, unique) - Citizenship number
- `wealth_class` (enum) - `rich`, `medium`, `poor`
- `membership_type` (enum) - `general`, `lifetime`, `institutional`, `special`, `other`
- `membership_status` (enum) - `active`, `inactive`, `cancelled`
- `date_joined` (date) - Membership date
- `status` (enum) - `active`, `inactive`
- `population_male` (integer) - Male population count
- `population_female` (integer) - Female population count
- `livestock_cattle` (integer)
- `livestock_buffalo` (integer)
- `livestock_goat` (integer)
- `education_level` (enum) - `illiterate`, `basic`, `secondary_plus`
- `occupation` (string, blank)
- `caste_ethnicity` (string, blank)
- `registration_date` (date)
- `entry_fee_type` (enum) - `new_household`, `split_household`
- `entry_fee_due` (decimal, read-only) - Calculated based on entry fee type
- `photo` (file, optional) - Household head photo
- `created_at` (datetime, read-only)
- `updated_at` (datetime, read-only)

### Member
Represents an individual member linked to a household.

**Attributes:**
- `id` (integer, read-only)
- `household` (integer, FK) - Household ID
- `household_name` (string, read-only) - Household head name
- `user` (integer, FK, optional) - Associated user account
- `user_email` (string, read-only) - User's email
- `full_name` (string, max 255)
- `created_at` (datetime, read-only)
- `updated_at` (datetime, read-only)

### MembershipRenewal
Tracks annual membership renewals and fee payments.

**Attributes:**
- `id` (integer, read-only)
- `member` (integer, FK) - Member ID
- `member_name` (string, read-only)
- `fiscal_year` (string) - Format: "YYYY/YY" (e.g., "2083/84")
- `fee_tier` (enum, read-only) - `on_time`, `overdue_3yr`, `overdue_5yr`, `overdue_5yr_plus`
- `fee_charged` (decimal, read-only) - Amount charged for renewal
- `paid_date` (date) - Payment date
- `created_at` (datetime, read-only)
- `updated_at` (datetime, read-only)

---

## Endpoints

### 1. Households

#### List Households
```
GET /api/members/households/
```

**Permissions:** `IsCommitteeOfficer | IsMember | IsSubCommitteeMember | IsDFOViewer`

**Query Parameters:**
- `wealth_class` - Filter by wealth class: `rich`, `medium`, `poor`
- `tole` - Filter by tole/village name
- `status` - Filter by status: `active`, `inactive`
- `search` - Search by household head name or tole
- `page` - Pagination page number

**Response:**
```json
{
  "count": 125,
  "next": "http://api/members/households/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "household_head_name": "Ram Kumar Sharma",
      "tole": "Bhagwati Tole",
      "citizenship_no": "56789-2087-123456",
      "wealth_class": "medium",
      "membership_type": "general",
      "membership_status": "active",
      "date_joined": "2020-05-15",
      "status": "active",
      "population_male": 3,
      "population_female": 2,
      "livestock_cattle": 2,
      "livestock_buffalo": 1,
      "livestock_goat": 0,
      "education_level": "secondary_plus",
      "occupation": "Farmer",
      "caste_ethnicity": "Brahmin",
      "registration_date": "2020-05-15",
      "entry_fee_type": "new_household",
      "entry_fee_due": "5000.00",
      "photo": "https://api/media/household_head_photos/...",
      "created_at": "2020-05-15T10:30:00Z",
      "updated_at": "2024-01-20T15:45:00Z"
    }
  ]
}
```

#### Get Household Details
```
GET /api/members/households/{id}/
```

**Permissions:** `IsCommitteeOfficer | IsMember | IsSubCommitteeMember | IsDFOViewer`

**Response:** Single household object (see List response format)

#### Create Household
```
POST /api/members/households/
```

**Permissions:** `IsCommitteeOfficer`

**Request Body:**
```json
{
  "household_head_name": "Ram Kumar Sharma",
  "tole": "Bhagwati Tole",
  "citizenship_no": "56789-2087-123456",
  "wealth_class": "medium",
  "membership_type": "general",
  "membership_status": "active",
  "date_joined": "2020-05-15",
  "status": "active",
  "population_male": 3,
  "population_female": 2,
  "livestock_cattle": 2,
  "livestock_buffalo": 1,
  "livestock_goat": 0,
  "education_level": "secondary_plus",
  "occupation": "Farmer",
  "caste_ethnicity": "Brahmin",
  "registration_date": "2020-05-15",
  "entry_fee_type": "new_household"
}
```

#### Update Household
```
PUT /api/members/households/{id}/
PATCH /api/members/households/{id}/
```

**Permissions:** `IsCommitteeOfficer`

#### Delete Household
```
DELETE /api/members/households/{id}/
```

**Permissions:** `IsCommitteeOfficer`

**Note:** Households with members cannot be deleted.

---

### 2. Members

#### List Members
```
GET /api/members/members/
```

**Permissions:** `IsCommitteeOfficer | IsMember | IsSubCommitteeMember | IsDFOViewer`

**Query Parameters:**
- `household` - Filter by household ID
- `household__wealth_class` - Filter by household wealth class
- `household__membership_type` - Filter by membership type
- `household__membership_status` - Filter by membership status
- `search` - Search by member name or citizenship number
- `page` - Pagination page number

**List Response (Lightweight):**
```json
{
  "count": 250,
  "results": [
    {
      "id": 1,
      "full_name": "Ram Kumar Sharma",
      "household_name": "Ram Kumar Sharma"
    }
  ]
}
```

#### Get Member Details
```
GET /api/members/members/{id}/
```

**Permissions:** `IsCommitteeOfficer | IsMember | IsSubCommitteeMember | IsDFOViewer`

**Detail Response:**
```json
{
  "id": 1,
  "household": 1,
  "household_name": "Ram Kumar Sharma",
  "user_email": "ram.sharma@example.com",
  "full_name": "Ram Kumar Sharma",
  "created_at": "2020-05-15T10:30:00Z",
  "updated_at": "2024-01-20T15:45:00Z"
}
```

#### Create Member
```
POST /api/members/members/
```

**Permissions:** `IsCommitteeOfficer`

**Request Body:**
```json
{
  "household": 1,
  "user": null,
  "full_name": "Sita Sharma"
}
```

#### Update Member
```
PUT /api/members/members/{id}/
PATCH /api/members/members/{id}/
```

**Permissions:** `IsCommitteeOfficer | Own member profile`

**Request Body:**
```json
{
  "full_name": "Sita Sharma Updated",
  "user": 5
}
```

#### Delete Member
```
DELETE /api/members/members/{id}/
```

**Permissions:** `IsCommitteeOfficer`

---

### 3. Membership Renewals

#### List Membership Renewals
```
GET /api/members/membership-renewals/
```

**Permissions:** `IsCommitteeOfficer`

**Query Parameters:**
- `fiscal_year` - Filter by fiscal year (e.g., "2083/84")
- `fee_tier` - Filter by fee tier: `on_time`, `overdue_3yr`, `overdue_5yr`, `overdue_5yr_plus`
- `search` - Search by member name or citizenship number
- `page` - Pagination page number

**Response:**
```json
{
  "count": 150,
  "results": [
    {
      "id": 1,
      "member": 5,
      "member_name": "Ram Kumar Sharma",
      "fiscal_year": "2083/84",
      "fee_tier": "on_time",
      "fee_charged": "500.00",
      "paid_date": "2026-06-15",
      "created_at": "2026-06-15T10:30:00Z",
      "updated_at": "2026-06-15T10:30:00Z"
    }
  ]
}
```

#### Get Renewal Details
```
GET /api/members/membership-renewals/{id}/
```

**Permissions:** `IsCommitteeOfficer`

#### Create Renewal (Administrative)
```
POST /api/members/membership-renewals/
```

**Permissions:** `IsCommitteeOfficer`

**Request Body:**
```json
{
  "member": 5,
  "fiscal_year": "2083/84",
  "fee_charged": "500.00",
  "paid_date": "2026-06-15"
}
```

**Note:** `fee_tier` and `fee_charged` are calculated automatically based on renewal rules.

#### Update Renewal
```
PUT /api/members/membership-renewals/{id}/
PATCH /api/members/membership-renewals/{id}/
```

**Permissions:** `IsCommitteeOfficer`

#### Delete Renewal
```
DELETE /api/members/membership-renewals/{id}/
```

**Permissions:** `IsCommitteeOfficer`

---

### 4. Household Details Statistics

#### List Households with Statistics
```
GET /api/members/household-stats/
```

**Permissions:** `IsCommitteeOfficer | IsDFOViewer`

**Query Parameters:**
- `wealth_class` - Filter by wealth class: `rich`, `medium`, `poor`
- `status` - Filter by household status: `active`, `inactive`
- `membership_type` - Filter by membership type
- `membership_status` - Filter by membership status
- `search` - Search by household head name, tole, or citizenship number
- `page` - Pagination page number

#### Get Household Details with Member Data
```
GET /api/members/household-stats/{id}/
```

**Permissions:** `IsCommitteeOfficer | IsDFOViewer`

**Response:** Household with aggregated member statistics
```json
{
  "id": 1,
  "household_head_name": "Ram Kumar Sharma",
  "tole": "Bhagwati Tole",
  "citizenship_no": "56789-2087-123456",
  "wealth_class": "medium",
  "membership_type": "general",
  "membership_status": "active",
  "date_joined": "2020-05-15",
  "status": "active",
  "population_male": 3,
  "population_female": 2,
  
  "members": [
    {
      "id": 1,
      "full_name": "Ram Kumar Sharma",
      "user_email": "ram@example.com",
      "created_at": "2020-05-15T10:30:00Z"
    },
    {
      "id": 2,
      "full_name": "Sita Sharma",
      "user_email": null,
      "created_at": "2020-05-15T10:30:00Z"
    }
  ],
  
  "total_members": 2,
  "member_list": ["Ram Kumar Sharma", "Sita Sharma"],
  
  "total_renewals": 3,
  "total_renewal_fees_paid": "1500.00",
  "avg_fee_per_renewal": "500.00",
  "members_with_renewals": 1,
  
  "total_committee_roles": 1,
  "total_candidacies": 0,
  
  "total_fee_collections": 5,
  "total_fees_collected": "2500.00",
  
  "total_harvest_requests": 3,
  "total_approved_requests": 2,
  "total_pending_requests": 1,
  
  "total_sales": 2,
  "total_sales_amount": "5000.00",
  
  "total_offense_reports_filed": 1,
  "total_informant_rewards_received": "500.00",
  "total_patrol_logs": 4,
  
  "total_revolving_loans": 1,
  "total_loan_amount": "10000.00",
  "total_livelihood_programs": 2,
  
  "created_at": "2020-05-15T10:30:00Z",
  "updated_at": "2024-01-20T15:45:00Z"
}
```

---

### 5. Member Details Statistics

#### Get Member Detailed Stats
```
GET /api/members/member-stats/{id}/
```

**Permissions:** `IsCommitteeOfficer | IsDFOViewer`

**Response:** Detailed member profile with individual statistics
```json
{
  "id": 1,
  "full_name": "Ram Kumar Sharma",
  "household_details": { /* Full household object */ },
  "user_email": "ram.sharma@example.com",
  "user_role": "MEMBER",
  
  "renewals_count": 3,
  "total_renewal_fees_paid": "1500.00",
  "last_renewal": {
    "fiscal_year": "2083/84",
    "fee_tier": "on_time",
    "fee_charged": "500.00",
    "paid_date": "2026-06-15"
  },
  "current_fee_tier": "on_time",
  
  "committee_roles_count": 1,
  "candidacies_count": 0,
  
  "fee_collections_count": 5,
  "total_fees_collected": "2500.00",
  
  "harvest_requests_count": 3,
  "harvest_requests_approved": 2,
  "harvest_requests_pending": 1,
  
  "sales_count": 2,
  "total_sales_amount": "5000.00",
  
  "offense_reports_filed": 1,
  "informant_rewards_received": "500.00",
  "patrol_logs_count": 4,
  
  "revolving_loans_count": 1,
  "revolving_loans_amount": "10000.00",
  "livelihood_programs_count": 2
}
```

---

### 6. Aggregate Household Statistics

#### Get Overall Household Statistics
```
GET /api/members/stats/aggregate/
```

**Permissions:** `IsCommitteeOfficer | IsDFOViewer`

**Query Parameters:**
- `status` - Filter by household status
- `wealth_class` - Filter by wealth class
- `membership_type` - Filter by membership type
- `membership_status` - Filter by membership status

**Response:**
```json
{
  "total_households": 125,
  "active_households": 115,
  "inactive_households": 10,
  
  "general_households": 100,
  "lifetime_households": 15,
  "institutional_households": 8,
  "special_households": 2,
  
  "active_memberships": 115,
  "inactive_memberships": 8,
  "cancelled_memberships": 2,
  
  "rich_households": 25,
  "medium_households": 75,
  "poor_households": 25,
  
  "total_members": 250,
  "avg_members_per_household": 2.0,
  
  "total_renewals": 280,
  "total_renewal_fees": "140000.00",
  
  "total_committee_roles": 25,
  "total_candidacies": 8,
  
  "total_fee_collections": 150,
  "total_collected_amount": "75000.00",
  
  "total_harvest_requests": 45,
  "approved_requests": 35,
  "pending_requests": 10,
  
  "total_sales": 30,
  "total_sales_amount": "150000.00",
  
  "total_offense_reports": 5,
  "total_informant_rewards": "2500.00",
  "total_patrol_logs": 20,
  
  "total_revolving_loans": 15,
  "total_loan_amount": "150000.00",
  "total_livelihood_programs": 35
}
```

#### Get Statistics by Household Wealth Class
```
GET /api/members/stats/by_wealth_class/
```

**Permissions:** `IsCommitteeOfficer | IsDFOViewer`

**Response:**
```json
{
  "rich": {
    "label": "Rich",
    "household_count": 25,
    "total_members": 55,
    "active_households": 24,
    "inactive_households": 1
  },
  "medium": {
    "label": "Medium",
    "household_count": 75,
    "total_members": 155,
    "active_households": 70,
    "inactive_households": 5
  },
  "poor": {
    "label": "Poor",
    "household_count": 25,
    "total_members": 40,
    "active_households": 21,
    "inactive_households": 4
  }
}
```

#### Get Statistics by Membership Type
```
GET /api/members/stats/by_membership_type/
```

**Permissions:** `IsCommitteeOfficer | IsDFOViewer`

**Response:**
```json
{
  "general": {
    "label": "General",
    "household_count": 100,
    "total_members": 200,
    "active": 95,
    "inactive": 4,
    "cancelled": 1
  },
  "lifetime": {
    "label": "Lifetime",
    "household_count": 15,
    "total_members": 30,
    "active": 15,
    "inactive": 0,
    "cancelled": 0
  },
  "institutional": {
    "label": "Institutional",
    "household_count": 8,
    "total_members": 15,
    "active": 4,
    "inactive": 3,
    "cancelled": 1
  },
  "special": {
    "label": "Special",
    "household_count": 2,
    "total_members": 5,
    "active": 1,
    "inactive": 1,
    "cancelled": 0
  }
}
```

#### Get Statistics by Membership Status
```
GET /api/members/stats/by_status/
```

**Permissions:** `IsCommitteeOfficer | IsDFOViewer`

**Response:**
```json
{
  "active": {
    "label": "Active",
    "household_count": 115,
    "total_members": 235,
    "by_type": {
      "general": 95,
      "lifetime": 15,
      "institutional": 4,
      "special": 1
    }
  },
  "inactive": {
    "label": "Inactive",
    "household_count": 8,
    "total_members": 12,
    "by_type": {
      "general": 4,
      "lifetime": 0,
      "institutional": 3,
      "special": 1
    }
  },
  "cancelled": {
    "label": "Cancelled",
    "household_count": 2,
    "total_members": 3,
    "by_type": {
      "general": 1,
      "lifetime": 0,
      "institutional": 1,
      "special": 0
    }
  }
}
```

---

### 7. User Member Statistics

#### Get Member User Statistics
```
GET /api/members/user-stats/aggregate/
```

**Permissions:** `IsCommitteeOfficer | IsDFOViewer`

**Response:**
```json
{
  "total_member_users": 150,
  "active_member_users": 140,
  "inactive_member_users": 10,
  "member_users_with_profile": 140,
  "member_users_without_profile": 10,
  "member_users_in_households": 140,
  "member_users_on_committees": 15
}
```

---

## Filtering and Search

### Filter Syntax

**By Single Value:**
```
GET /api/members/households/?wealth_class=medium
```

**By Multiple Values (Query repeating):**
```
GET /api/members/households/?tole=Bhagwati&tole=Kathmandu
```

**Combined Filters:**
```
GET /api/members/members/?household__wealth_class=medium&household__membership_status=active
```

### Search Syntax

```
GET /api/members/households/?search=ram
GET /api/members/members/?search=sharma
```

---

## Pagination

All list endpoints support pagination:

```
GET /api/members/households/?page=2&page_size=50
```

**Response Header:**
```
X-Total-Count: 125
Link: <http://api/members/households/?page=2>; rel="next"
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid query parameters",
  "details": {
    "wealth_class": ["'invalid' is not a valid choice"]
  }
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error"
}
```

---

## Enum Values

### Wealth Class
- `rich` - Rich
- `medium` - Medium
- `poor` - Poor

### Membership Type
- `general` - General
- `lifetime` - Lifetime
- `institutional` - Institutional
- `special` - Special
- `other` - Other

### Membership Status
- `active` - Active
- `inactive` - Inactive
- `cancelled` - Cancelled

### Household Status
- `active` - Active
- `inactive` - Inactive

### Education Level
- `illiterate` - Illiterate
- `basic` - Basic
- `secondary_plus` - Secondary+

### Entry Fee Type
- `new_household` - New household
- `split_household` - Split household

### Fee Tier (Renewal)
- `on_time` - On time (0-1 years overdue)
- `overdue_3yr` - Overdue up to 3 years
- `overdue_5yr` - Overdue up to 5 years
- `overdue_5yr_plus` - Overdue more than 5 years

---

## Common Use Cases

### 1. Get household with aggregated member statistics
```
GET /api/members/household-stats/1/
```

### 2. Get all wealthy households with their members
```
GET /api/members/household-stats/?wealth_class=rich
```

### 3. Search for a specific household
```
GET /api/members/households/?search=ram%20kumar
```

### 4. Get member details and their personal statistics
```
GET /api/members/member-stats/1/
```

### 5. Get overall statistics across all households
```
GET /api/members/stats/aggregate/
```

### 6. Get household statistics grouped by wealth class with member counts
```
GET /api/members/stats/by_wealth_class/
```

### 7. Get all renewal records for a specific fiscal year
```
GET /api/members/membership-renewals/?fiscal_year=2083/84
```

### 8. Get households with inactive membership status
```
GET /api/members/household-stats/?membership_status=inactive
```

### 9. Create a new household with initial member
```
POST /api/members/households/
{
  "household_head_name": "New Household Head",
  "citizenship_no": "12345-2080-654321",
  "wealth_class": "medium",
  "membership_type": "general",
  "membership_status": "active",
  "date_joined": "2026-07-08",
  "registration_date": "2026-07-08",
  "status": "active"
}

POST /api/members/members/
{
  "household": {returned_household_id},
  "full_name": "Household Member Name"
}
```

### 10. Get statistics of households by membership type with member breakdown
```
GET /api/members/stats/by_membership_type/
```

---

## Rate Limiting

Rate limits are applied per authenticated user:
- **Default:** 1000 requests per hour
- **List endpoints:** 5000 requests per hour

---

## Versioning

Current API version: **v1**

Future breaking changes will be available at `/api/v2/members/`

---

## Notes

- All timestamps are in UTC (ISO 8601 format)
- Decimal fields use 2 decimal places
- **Household-Centric Statistics**: All statistics are organized at the household level with aggregated member data
- Membership status is managed at the Household level
- Members inherit membership properties from their household
- `HouseholdDetailStatsViewSet` (`/household-stats/`) provides household-level view with all members and aggregated metrics
- `MemberDetailStatsViewSet` (`/member-stats/`) provides individual member statistics for detailed member analysis
- `HouseholdStatsViewSet` (`/stats/`) provides aggregate statistics across all households with member data aggregation
- Renewal fees are calculated automatically based on configured rates
- Member users can only access their own profile data
- Statistics include cross-system data: renewals, fees, harvests, sales, governance, offenses, and livelihood programs
