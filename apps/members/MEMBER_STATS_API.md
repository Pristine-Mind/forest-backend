# Member Statistics API Documentation

## Overview

This document describes the comprehensive statistics APIs for members and users with member role. These endpoints provide detailed information about member data and all their system associations.

## Base URL

```
/api/members/
```

## Authentication

All endpoints require authentication and appropriate permissions:
- **Required Role**: Committee Officer or DFO Viewer
- **Auth Header**: `Authorization: Bearer <token>`

---

## Endpoints

### 1. Member Detail Statistics

Get detailed statistics for a specific member including all system associations.

#### Request

```http
GET /api/members/members-stats/{member_id}/
Authorization: Bearer <token>
```

#### Response (200 OK)

```json
{
  "id": 1,
  "full_name": "John Doe",
  "citizenship_no": "123456789",
  "membership_type": "general",
  "membership_status": "active",
  "date_joined": "2020-01-15",
  "household_details": {
    "id": 1,
    "household_head_name": "John Doe",
    "tole": "Daman",
    "wealth_class": "medium",
    "population_male": 2,
    "population_female": 3,
    "livestock_cattle": 2,
    "livestock_buffalo": 1,
    "livestock_goat": 5,
    "education_level": "basic",
    "occupation": "Farmer",
    "caste_ethnicity": "Rai",
    "registration_date": "2020-01-15",
    "entry_fee_type": "new_household",
    "entry_fee_due": "100.00",
    "status": "active"
  },
  "user_email": "john@example.com",
  "user_role": "member",
  
  "renewals_count": 3,
  "total_renewal_fees_paid": "150.00",
  "last_renewal": {
    "fiscal_year": "2082/83",
    "fee_tier": "on_time",
    "fee_charged": "50.00",
    "paid_date": "2023-08-15"
  },
  "current_fee_tier": "on_time",
  
  "committee_roles_count": 1,
  "candidacies_count": 0,
  
  "fee_collections_count": 3,
  "total_fees_collected": "200.00",
  
  "harvest_requests_count": 2,
  "harvest_requests_approved": 1,
  "harvest_requests_pending": 1,
  
  "sales_count": 5,
  "total_sales_amount": "5000.00",
  
  "offense_reports_filed": 2,
  "informant_rewards_received": "500.00",
  "patrol_logs_count": 10,
  
  "revolving_loans_count": 1,
  "revolving_loans_amount": "10000.00",
  "livelihood_programs_count": 2,
  
  "created_at": "2020-01-15T10:30:00Z",
  "updated_at": "2024-07-06T15:45:00Z"
}
```

#### Query Parameters

- `membership_type` - Filter by membership type: `general`, `lifetime`, `institutional`, `special`, `other`
- `membership_status` - Filter by status: `active`, `inactive`, `cancelled`
- `wealth_class` - Filter by household wealth class: `rich`, `medium`, `poor`
- `search` - Search by full name or citizenship number

#### Example

```bash
curl -H "Authorization: Bearer token" \
  "http://localhost:8000/api/members/members-stats/1/?membership_status=active"
```

---

### 2. Member Aggregate Statistics

Get aggregate statistics across all or filtered members.

#### Request

```http
GET /api/members/stats/aggregate/
Authorization: Bearer <token>
```

#### Response (200 OK)

```json
{
  "total_members": 150,
  "active_members": 140,
  "inactive_members": 8,
  "cancelled_members": 2,
  "general_members": 100,
  "lifetime_members": 30,
  "institutional_members": 15,
  "special_members": 5,
  "rich_households": 30,
  "medium_households": 70,
  "poor_households": 50,
  "total_renewals": 280,
  "total_renewal_fees": "14000.00",
  "total_committee_roles": 15,
  "total_candidacies": 8,
  "total_fee_collections": 150,
  "total_collected_amount": "25000.00",
  "total_harvest_requests": 45,
  "approved_requests": 38,
  "pending_requests": 7,
  "total_sales": 200,
  "total_sales_amount": "150000.00",
  "total_offense_reports": 12,
  "total_informant_rewards": "6000.00",
  "total_patrol_logs": 350,
  "total_revolving_loans": 25,
  "total_loan_amount": "250000.00",
  "total_livelihood_programs": 60
}
```

#### Query Parameters (Optional Filters)

- `status` - Filter by membership status: `active`, `inactive`, `cancelled`
- `wealth_class` - Filter by household wealth class: `rich`, `medium`, `poor`
- `membership_type` - Filter by membership type

#### Example

```bash
# Get stats for active members only
curl -H "Authorization: Bearer token" \
  "http://localhost:8000/api/members/stats/aggregate/?status=active"

# Get stats for poor households
curl -H "Authorization: Bearer token" \
  "http://localhost:8000/api/members/stats/aggregate/?wealth_class=poor"
```

---

### 3. Members by Wealth Class

Get member statistics grouped by household wealth class.

#### Request

```http
GET /api/members/stats/by_wealth_class/
Authorization: Bearer <token>
```

#### Response (200 OK)

```json
{
  "rich": {
    "label": "Rich",
    "count": 30,
    "active": 28,
    "inactive": 2,
    "cancelled": 0
  },
  "medium": {
    "label": "Medium",
    "count": 70,
    "active": 65,
    "inactive": 4,
    "cancelled": 1
  },
  "poor": {
    "label": "Poor",
    "count": 50,
    "active": 47,
    "inactive": 2,
    "cancelled": 1
  }
}
```

---

### 4. Members by Membership Type

Get member statistics grouped by membership type.

#### Request

```http
GET /api/members/stats/by_membership_type/
Authorization: Bearer <token>
```

#### Response (200 OK)

```json
{
  "general": {
    "label": "General",
    "count": 100,
    "active": 95,
    "inactive": 4,
    "cancelled": 1
  },
  "lifetime": {
    "label": "Lifetime",
    "count": 30,
    "active": 30,
    "inactive": 0,
    "cancelled": 0
  },
  "institutional": {
    "label": "Institutional",
    "count": 15,
    "active": 12,
    "inactive": 2,
    "cancelled": 1
  },
  "special": {
    "label": "Special",
    "count": 5,
    "active": 3,
    "inactive": 2,
    "cancelled": 0
  }
}
```

---

### 5. Members by Status

Get member statistics grouped by membership status.

#### Request

```http
GET /api/members/stats/by_status/
Authorization: Bearer <token>
```

#### Response (200 OK)

```json
{
  "active": {
    "label": "Active",
    "count": 140,
    "by_type": {
      "general": 95,
      "lifetime": 30,
      "institutional": 12,
      "special": 3
    }
  },
  "inactive": {
    "label": "Inactive",
    "count": 8,
    "by_type": {
      "general": 4,
      "lifetime": 0,
      "institutional": 2,
      "special": 2
    }
  },
  "cancelled": {
    "label": "Cancelled",
    "count": 2,
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

### 6. User Member Statistics

Get aggregate statistics for users with member role.

#### Request

```http
GET /api/members/user-stats/aggregate/
Authorization: Bearer <token>
```

#### Response (200 OK)

```json
{
  "total_member_users": 100,
  "active_member_users": 95,
  "inactive_member_users": 5,
  "member_users_with_profile": 95,
  "member_users_without_profile": 5,
  "member_users_in_households": 95,
  "member_users_on_committees": 15
}
```

---

## Member Associations Overview

Each member is connected to various parts of the system:

### Core Member Data
- **Household**: Demographic, economic, and livestock information
- **User Account**: Authentication and system access
- **Membership Renewals**: Annual fee payments and status

### Governance
- **Committee Roles**: Leadership positions held
- **Candidacies**: Electoral participation

### Billing & Finance
- **Fee Collections**: Membership and renewal fees paid
- **Revolving Loans**: Household livelihood loans
- **Livelihood Programs**: Poverty-targeted programs

### Forest Resources
- **Harvest Requests**: Forest product collection requests
- **Sales**: Timber and product sales
- **Patrols**: Forest monitoring activities

### Compliance
- **Offense Reports**: Violations filed by members
- **Informant Rewards**: Rewards for providing offense information
- **Audit Logs**: Administrative action tracking

---

## Field Definitions

### Member Fields
| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Unique member identifier |
| full_name | String | Member's full name |
| citizenship_no | String | Citizenship number (unique) |
| membership_type | Enum | general, lifetime, institutional, special, other |
| membership_status | Enum | active, inactive, cancelled |
| date_joined | Date | Member registration date |

### Renewal Fields
| Field | Type | Description |
|-------|------|-------------|
| renewals_count | Integer | Total renewal records |
| total_renewal_fees_paid | Decimal | Sum of all renewal fees |
| last_renewal | Object | Most recent renewal details |
| current_fee_tier | Enum | on_time, overdue_3yr, overdue_5yr, overdue_5yr_plus |

### Association Count Fields
| Field | Type | Description |
|-------|------|-------------|
| committee_roles_count | Integer | Number of committee positions |
| candidacies_count | Integer | Number of election candidacies |
| fee_collections_count | Integer | Number of fee payments |
| harvest_requests_count | Integer | Number of harvest requests |
| sales_count | Integer | Number of sales records |
| offense_reports_filed | Integer | Offenses reported by member |
| informant_rewards_received | Decimal | Total rewards earned |
| patrol_logs_count | Integer | Number of patrol participations |
| revolving_loans_count | Integer | Household loans |
| livelihood_programs_count | Integer | Livelihood program participations |

---

## Error Responses

### 403 Forbidden

```json
{
  "detail": "You do not have permission to perform this action."
}
```

**Occurs when**:
- User lacks Committee Officer or DFO Viewer role
- Attempting to access restricted statistics

### 404 Not Found

```json
{
  "detail": "Not found."
}
```

**Occurs when**:
- Member ID does not exist
- Invalid resource reference

---

## Usage Examples

### Get Complete Profile for Specific Member

```bash
curl -X GET \
  "http://localhost:8000/api/members/members-stats/42/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### Get Stats for Active Members in Poor Households

```bash
curl -X GET \
  "http://localhost:8000/api/members/stats/aggregate/?status=active&wealth_class=poor" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### Check Member User Demographics

```bash
curl -X GET \
  "http://localhost:8000/api/members/user-stats/aggregate/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

---

## Permissions & Access Control

| Endpoint | Committee Officer | DFO Viewer | Member | Sub-Committee |
|----------|-------------------|-----------|--------|---------------|
| members-stats (detail) | ✓ | ✓ | ✗ | ✗ |
| stats/aggregate | ✓ | ✓ | ✗ | ✗ |
| stats/by_wealth_class | ✓ | ✓ | ✗ | ✗ |
| stats/by_membership_type | ✓ | ✓ | ✗ | ✗ |
| stats/by_status | ✓ | ✓ | ✗ | ✗ |
| user-stats/aggregate | ✓ | ✓ | ✗ | ✗ |

---

## Performance Notes

- Detail stats endpoint fetches all related data; consider caching for large datasets
- Aggregate endpoints use efficient database queries with appropriate indexing
- Filter parameters significantly reduce query overhead
- All endpoints support pagination (limit, offset) via Django REST framework
