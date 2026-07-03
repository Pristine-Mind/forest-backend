# Forest Backend — Complete API Data Types, Permissions & Integration Guide

> **Audience:** Frontend / mobile engineers consuming the Forest Management System Django REST Framework backend.  
> **Last updated:** 2026-06-24  
> **Base URL:** `/api/v1/`

This document contains **every endpoint**, its exact **request/response TypeScript shapes**, the **permissions** required, filter/search parameters, and a step-by-step integration guide.

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [Authentication](#2-authentication)
3. [Permission System](#3-permission-system)
4. [Common Types](#4-common-types)
5. [Core API](#5-core-api)
6. [Members API](#6-members-api)
7. [Forest API](#7-forest-api)
8. [Harvest API](#8-harvest-api)
9. [Inventory API](#9-inventory-api)
10. [Visitors API](#10-visitors-api)
11. [Billing API](#11-billing-api)
12. [Governance API](#12-governance-api)
13. [Fund API](#13-fund-api)
14. [Livelihood API](#14-livelihood-api)
15. [Offense API](#15-offense-api)
16. [Reports API](#16-reports-api)
17. [Step-by-Step Integration](#17-step-by-step-integration)
18. [Zod Schemas](#18-zod-schemas)
19. [Permission Guards](#19-permission-guards)
20. [Error Handling](#20-error-handling)

---

## 1. Quick Start

All endpoints share the prefix `/api/v1/<app>/`.

| App | Prefix |
|-----|--------|
| Core | `/api/v1/core/` |
| Members | `/api/v1/members/` |
| Forest | `/api/v1/forest/` |
| Harvest | `/api/v1/harvest/` |
| Inventory | `/api/v1/inventory/` |
| Visitors | `/api/v1/visitors/` |
| Billing | `/api/v1/billing/` |
| Governance | `/api/v1/governance/` |
| Fund | `/api/v1/fund/` |
| Livelihood | `/api/v1/livelihood/` |
| Offense | `/api/v1/offense/` |
| Reports | `/api/v1/reports/` |

### Global settings

- **Authentication:** `TokenAuthentication` + `SessionAuthentication`
- **Token header:** `Authorization: Token <key>`
- **Pagination:** DRF `LimitOffsetPagination`, default `PAGE_SIZE = 100`
- **Filter backends:** `DjangoFilterBackend`, `SearchFilter`, `OrderingFilter`

### Paginated response shape

```ts
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
```

### Standard CRUD shorthand

DRF `DefaultRouter` creates these routes for every `ModelViewSet`:

| Method | URL | Action |
|--------|-----|--------|
| GET | `/` | list |
| POST | `/` | create |
| GET | `/{id}/` | retrieve |
| PUT | `/{id}/` | update |
| PATCH | `/{id}/` | partial_update |
| DELETE | `/{id}/` | destroy |

Unless noted otherwise, all ViewSets support these actions.

---

## 2. Authentication

### POST `/api/v1/core/auth/login/`

**Permission:** Public (`AllowAny`).  
**Request:**

```ts
export interface LoginRequest {
  email: string;
  password: string;
}
```

**Response:**

```ts
export interface LoginResponse {
  token: string;
  user: User;
}
```

### POST `/api/v1/core/auth/logout/`

**Permission:** `IsAuthenticated`.  
**Request:** empty body.  
**Response:** `{ detail: string }` (deletes the DRF Token).

### GET `/api/v1/core/users/me/`

**Permission:** `IsAuthenticated`.  
**Response:** `User`.

---

## 3. Permission System

Custom permissions live in `apps/core/permissions.py`. They are combined with DRF's bitwise `|` operator (logical OR).

| Permission | Code role | Effect |
|------------|-----------|--------|
| `IsCommitteeOfficer` | `committee_officer`, `admin`, superuser | Full CRUD on the resource. |
| `IsAuthenticatedReadOnly` | any authenticated user | Read-only (`GET`, `HEAD`, `OPTIONS`) only. |
| `IsMember` | `member` + officers | Member can read own household/member data; officers get full access. |
| `IsSubCommitteeMember` | `sub_committee_member`, officers, DFO viewers | Scoped access; officers/DFO get read/write where configured. |
| `IsDFOViewer` | `dfo_viewer`, superuser | Read-only all data (only on endpoints that include it). |

### Effective role matrix

| Endpoint pattern | Officer/Admin | Member | Sub-committee | DFO Viewer | Authenticated |
|------------------|---------------|--------|---------------|------------|---------------|
| Most inventory/forest/visitors/reports | CRUD | Read-only | Read-only | Read-only | Read-only |
| Members household/member | CRUD | Own record read | Own record read | Read-only | Read-only |
| Harvest requests | CRUD + approve/reject | Own requests CRUD | Read-only | Read-only | Read-only |
| Fund allocation / public audits | CRUD | Read-only | Read-only | Read-only | Read-only |
| Fund bank accounts / cash / audits | CRUD | Read-only | CRUD* | Read-only | Read-only |
| Livelihood records | CRUD | Own household read | All read | Read-only | Read-only |
| Governance (except handover) | CRUD | Read-only | Read-only | Read-only | Read-only |
| Governance handover records | CRUD | — | — | — | — |
| Billing fee collections | CRUD | Read-only | Read-only | Read-only | Read-only |
| Billing receipts | Read-only | Read-only | Read-only | Read-only | Read-only |
| Offense reports | CRUD + resolve | Create own + read | Read/write evidence/hearings/patrol | Read-only | Read-only |
| Offense informant rewards | Read-only | Read-only | Read-only | Read-only | Read-only |

> \* Fund bank-accounts, cash-transactions and audits also allow `IsSubCommitteeMember`.

---

## 4. Common Types

```ts
export type UserRole =
  | 'committee_officer'
  | 'member'
  | 'sub_committee_member'
  | 'dfo_viewer'
  | 'admin';

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_active: boolean;
  date_joined: string; // ISO date
}

export interface UserCreateInput {
  email: string;
  first_name?: string;
  last_name?: string;
  role: UserRole;
  password: string; // min 8 chars, write-only
  is_active?: boolean;
}

export interface AuditFields {
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiValidationError {
  [field: string]: string[];
}
```

---

## 5. Core API

Base: `/api/v1/core/`

### Users (`/users/`)

**Permission:** `IsCommitteeOfficer` for CRUD. `GET /users/me/` uses `IsAuthenticated`.

```ts
export interface UserListItem {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_active: boolean;
  date_joined: string;
}
```

| Method | Endpoint | Body | Response |
|--------|----------|------|----------|
| GET | `/users/` | — | `PaginatedResponse<UserListItem>` |
| POST | `/users/` | `UserCreateInput` | `UserListItem` |
| GET | `/users/{id}/` | — | `UserListItem` |
| PUT/PATCH | `/users/{id}/` | `Partial<UserCreateInput>` (omit password on update) | `UserListItem` |
| DELETE | `/users/{id}/` | — | `204 No Content` |
| GET | `/users/me/` | — | `UserListItem` |

**Search:** `email`, `first_name`, `last_name`.

### System Config (`/system-config/`)

**Permission:** `IsCommitteeOfficer` (retrieve + update only).

```ts
export interface SystemConfig {
  id: number;
  new_household_entry_fee: string; // decimal string
  split_household_entry_fee: string;
  renewal_fee_on_time: string;
  renewal_fee_overdue_3yr: string;
  renewal_fee_overdue_5yr: string;
  renewal_fee_overdue_5yr_plus: string;
  membership_cancellation_years: number;
  current_fiscal_year: string;
  forest_dev_min_percent: string;
  poor_targeted_min_percent: string;
  cash_chair_approval_limit: string;
  cash_treasurer_approval_limit: string;
  audit_external_threshold: string;
  informant_reward_percent: string;
  no_confidence_signature_percent: string;
  handover_deadline_days: number;
  min_female_committee_members: number;
  min_dalit_or_minority_committee_members: number;
}
```

| Method | Endpoint | Body | Response |
|--------|----------|------|----------|
| GET | `/system-config/` | — | `SystemConfig` |
| PUT/PATCH | `/system-config/` | `Partial<SystemConfig>` | `SystemConfig` |

---

## 6. Members API

Base: `/api/v1/members/`

### Households (`/households/`)

**Permission:** `IsCommitteeOfficer | IsMember | IsSubCommitteeMember | IsDFOViewer`.  
Members/Sub-committee see only their own household.

```ts
export type WealthClass = 'rich' | 'medium' | 'poor';
export type EducationLevel = 'illiterate' | 'basic' | 'secondary_plus';
export type EntryFeeType = 'new_household' | 'split_household';
export type HouseholdStatus = 'active' | 'inactive';

export interface Household {
  id: number;
  household_head_name: string;
  tole: string;
  wealth_class: WealthClass;
  population_male: number;
  population_female: number;
  livestock_cattle: number;
  livestock_buffalo: number;
  livestock_goat: number;
  education_level: EducationLevel | '';
  occupation: string;
  caste_ethnicity: string;
  registration_date: string; // ISO date
  entry_fee_type: EntryFeeType;
  entry_fee_due: string; // read-only decimal string
  status: HouseholdStatus;
  created_at: string;
  updated_at: string;
}

export type HouseholdInput = Omit<
  Household,
  'id' | 'entry_fee_due' | 'created_at' | 'updated_at'
>;
```

**Filters:** `wealth_class`, `tole`, `status`.  
**Search:** `household_head_name`, `tole`.

### Members (`/members/`)

**Permission:** same as households.  
Members/Sub-committee see only their own member record.

```ts
export type MembershipType = 'general' | 'lifetime' | 'institutional' | 'special' | 'other';
export type MembershipStatus = 'active' | 'inactive' | 'cancelled';

export interface Member {
  id: number;
  household: number; // FK
  household_name: string; // read-only
  user: number | null; // FK to core.User
  user_email: string | null; // read-only
  full_name: string;
  citizenship_no: string;
  membership_type: MembershipType;
  membership_status: MembershipStatus;
  date_joined: string;
  created_at: string;
  updated_at: string;
}

export interface MemberListItem {
  id: number;
  full_name: string;
  citizenship_no: string;
  membership_status: MembershipStatus;
  household_name: string;
}

export type MemberInput = Omit<
  Member,
  'id' | 'household_name' | 'user_email' | 'created_at' | 'updated_at'
>;
```

**Filters:** `membership_type`, `membership_status`, `household__wealth_class`.  
**Search:** `full_name`, `citizenship_no`.  
**Note:** `GET /members/` returns `MemberListItem[]` (light list serializer). `GET /members/{id}/` returns full `Member`.

### Membership Renewals (`/membership-renewals/`)

**Permission:** `IsCommitteeOfficer` only.

```ts
export type FeeTier = 'on_time' | 'overdue_3yr' | 'overdue_5yr' | 'overdue_5yr_plus';

export interface MembershipRenewal {
  id: number;
  member: number; // FK
  member_name: string; // read-only
  fiscal_year: string;
  fee_tier: FeeTier; // read-only
  fee_charged: string; // read-only decimal string
  paid_date: string | null;
  created_at: string;
  updated_at: string;
}

export type MembershipRenewalInput = Omit<
  MembershipRenewal,
  'id' | 'member_name' | 'fee_tier' | 'fee_charged' | 'created_at' | 'updated_at'
>;
```

**Filters:** `fiscal_year`, `fee_tier`.  
**Search:** `member__full_name`, `member__citizenship_no`.

---

## 7. Forest API

Base: `/api/v1/forest/`

**Default permission:** `IsCommitteeOfficer | IsAuthenticatedReadOnly`.

### Forest Blocks (`/blocks/`)

```ts
export interface ForestBlock {
  id: number;
  block_name: string;
  area_hectares: string; // decimal string
  created_at: string;
  updated_at: string;
}

export type ForestBlockInput = Omit<ForestBlock, 'id' | 'created_at' | 'updated_at'>;
```

**Filter:** `block_name`.  
**Search:** `block_name`.

### Species (`/species/`)

```ts
export interface Species {
  id: number;
  species_name: string;
  created_at: string;
  updated_at: string;
}

export type SpeciesInput = Omit<Species, 'id' | 'created_at' | 'updated_at'>;
```

**Search:** `species_name`.

### Operational Plans (`/operational-plans/`)

```ts
export interface OperationalPlan {
  id: number;
  valid_from: string;
  valid_to: string;
  approved_harvest_limit: string; // decimal string
  description: string;
  created_at: string;
  updated_at: string;
}

export type OperationalPlanInput = Omit<
  OperationalPlan,
  'id' | 'created_at' | 'updated_at'
>;
```

**Filters:** `valid_from`, `valid_to`.

### Tree Count Registers (`/tree-counts/`)

```ts
export interface TreeCountRegister {
  id: number;
  species: number; // FK
  species_name: string; // read-only
  block: number | null; // FK
  block_name: string | null; // read-only
  total_count: number;
  harvested_count: number; // read-only
  remaining_count: number; // read-only computed property
  last_updated: string;
  adjustment_reason: string;
  created_at: string;
  updated_at: string;
}

export type TreeCountRegisterInput = Omit<
  TreeCountRegister,
  | 'id'
  | 'species_name'
  | 'block_name'
  | 'harvested_count'
  | 'remaining_count'
  | 'created_at'
  | 'updated_at'
>;
```

**Filters:** `species`, `block`.  
**Search:** `species__species_name`, `block__block_name`.

---

## 8. Harvest API

Base: `/api/v1/harvest/`

### Harvest Requests (`/requests/`)

**Permission:** `IsCommitteeOfficer | IsMember | IsAuthenticatedReadOnly`.  
Approve/reject actions are `IsCommitteeOfficer` only.

```ts
export type HarvestSourceType = 'member_requested' | 'forest_initiated';
export type HarvestStatus = 'pending' | 'approved' | 'rejected';

export interface HarvestRequest {
  id: number;
  source_type: HarvestSourceType;
  member: number | null; // FK to members.Member
  member_name: string | null; // read-only
  operation_name: string;
  species: number; // FK to forest.Species
  species_name: string; // read-only
  quantity: string; // decimal string
  status: HarvestStatus; // read-only
  requested_date: string;
  approved_by: number | null; // FK to core.User, read-only
  approved_by_name: string | null; // read-only
  notes: string;
  created_at: string;
  updated_at: string;
}

export type HarvestRequestInput = Omit<
  HarvestRequest,
  | 'id'
  | 'member_name'
  | 'species_name'
  | 'status'
  | 'approved_by'
  | 'approved_by_name'
  | 'created_at'
  | 'updated_at'
>;
```

**Validation rules:**

- If `source_type = 'member_requested'`: `member` is required; `operation_name` must be blank.
- If `source_type = 'forest_initiated'`: `member` must be blank; `operation_name` is required.

**Filters:** `source_type`, `status`, `species`, `requested_date`.  
**Search:** `member__full_name`, `species__species_name`, `operation_name`.

### Custom actions

| Method | Endpoint | Body | Permission | Response |
|--------|----------|------|------------|----------|
| POST | `/requests/{id}/approve/` | — | Officer | `{ status: 'approved' }` |
| POST | `/requests/{id}/reject/` | `{ notes: string }` | Officer | `{ status: string }` |

---

## 9. Inventory API

Base: `/api/v1/inventory/`

**Default permission:** `IsCommitteeOfficer | IsAuthenticatedReadOnly`.

### Stock Ledgers (`/ledgers/`)

```ts
export interface StockLedger {
  id: number;
  species: number; // FK
  species_name: string; // read-only
  grade: string;
  quantity_available: string; // read-only decimal string
  created_at: string;
  updated_at: string;
}

export type StockLedgerInput = Omit<
  StockLedger,
  'id' | 'species_name' | 'quantity_available' | 'created_at' | 'updated_at'
>;
```

**Filters:** `species`, `grade`.  
**Search:** `species__species_name`, `grade`.

### Stock Transactions (`/transactions/`)

```ts
export type StockTransactionType = 'in' | 'out';
export type StockTransactionReference = 'harvest' | 'sale' | 'adjustment';

export interface StockTransaction {
  id: number;
  stock: number; // FK to StockLedger
  transaction_type: StockTransactionType;
  quantity: string; // decimal string
  reference_type: StockTransactionReference; // read-only
  reference_id: number; // read-only
  note: string;
  created_at: string;
}

export type StockTransactionInput = Omit<
  StockTransaction,
  'id' | 'reference_type' | 'reference_id' | 'created_at'
>;
```

**Filters:** `stock`, `transaction_type`, `reference_type`.

### Price Rates (`/price-rates/`)

```ts
export type InventoryBuyerType = 'member' | 'outsider';

export interface PriceRate {
  id: number;
  species: number; // FK
  species_name: string; // read-only
  grade: string;
  buyer_type: InventoryBuyerType;
  rate_per_unit: string; // decimal string
  effective_from: string;
  created_at: string;
  updated_at: string;
}

export type PriceRateInput = Omit<
  PriceRate,
  'id' | 'species_name' | 'created_at' | 'updated_at'
>;
```

**Filters:** `species`, `grade`, `buyer_type`.

### Sales (`/sales/`)

```ts
export type SalePaymentStatus = 'paid' | 'due' | 'partial';

export interface Sale {
  id: number;
  buyer_name: string;
  buyer_type: InventoryBuyerType;
  member: number | null; // FK
  member_name: string | null; // read-only
  species: number; // FK
  species_name: string; // read-only
  grade: string;
  quantity: string; // decimal string
  rate_applied: string; // decimal string
  total_amount: string; // read-only decimal string
  payment_status: SalePaymentStatus;
  receipt_no: string | null; // read-only
  audit_note: string;
  created_at: string;
  updated_at: string;
}

export type SaleInput = Omit<
  Sale,
  | 'id'
  | 'member_name'
  | 'species_name'
  | 'total_amount'
  | 'receipt_no'
  | 'created_at'
  | 'updated_at'
>;
```

**Validation rules:**

- If `buyer_type = 'member'`: `member` is required.
- If `buyer_type = 'outsider'`: `member` must be blank.

**Filters:** `buyer_type`, `species`, `grade`, `payment_status`.  
**Search:** `buyer_name`, `member__full_name`.

### Record sale action

| Method | Endpoint | Body | Permission | Response |
|--------|----------|------|------------|----------|
| POST | `/sales/record/` | `SaleInput` | Officer | `Sale` |

---

## 10. Visitors API

Base: `/api/v1/visitors/`

**Default permission:** `IsCommitteeOfficer | IsAuthenticatedReadOnly`.

### Visitor Fee Rates (`/fee-rates/`)

```ts
export type VisitPurpose = 'general_visit' | 'study_research';

export interface VisitorFeeRate {
  id: number;
  visit_purpose: VisitPurpose;
  fee_per_visitor_per_day: string; // decimal string
  created_at: string;
  updated_at: string;
}

export type VisitorFeeRateInput = Omit<
  VisitorFeeRate,
  'id' | 'created_at' | 'updated_at'
>;
```

### Visitor Entries (`/entries/`)

```ts
export interface VisitorEntry {
  id: number;
  entry_date: string;
  visit_purpose: VisitPurpose;
  visitor_count: number;
  days: number;
  fee_waived: boolean;
  total_amount: string; // read-only decimal string
  receipt_no: string | null; // read-only
  created_at: string;
  updated_at: string;
}

export type VisitorEntryInput = Omit<
  VisitorEntry,
  'id' | 'total_amount' | 'receipt_no' | 'created_at' | 'updated_at'
>;
```

**Filters:** `entry_date`, `visit_purpose`, `fee_waived`.

### Log and collect action

| Method | Endpoint | Body | Permission | Response |
|--------|----------|------|------------|----------|
| POST | `/entries/log_and_collect/` | `VisitorEntryInput` | Officer | `VisitorEntry` |

### Official Guest Logs (`/official-guests/`)

```ts
export interface OfficialGuestLog {
  id: number;
  visitor_name: string;
  designation: string;
  visit_start_date: string;
  visit_end_date: string;
  comments_or_guidance: string;
  created_at: string;
  updated_at: string;
}

export type OfficialGuestLogInput = Omit<
  OfficialGuestLog,
  'id' | 'created_at' | 'updated_at'
>;
```

**Filters:** `visit_start_date`, `visit_end_date`.  
**Search:** `visitor_name`, `designation`.

---

## 11. Billing API

Base: `/api/v1/billing/`

### Receipts (`/receipts/`)

**Permission:** `IsCommitteeOfficer | IsAuthenticatedReadOnly` (read-only ViewSet).

```ts
export type ReceiptReferenceType = 'sale' | 'fee_collection' | 'visitor_entry';

export interface Receipt {
  receipt_no: string; // primary key, e.g. RCP-000001
  reference_type: ReceiptReferenceType;
  reference_id: number;
  amount: string; // decimal string
  issued_date: string;
  issued_by: number | null; // FK to core.User
  pdf_file: string | null; // URL path
  created_at: string;
}
```

**Filters:** `reference_type`, `issued_date`.  
**Search:** `receipt_no`.  
**Lookup field:** `receipt_no` (not numeric `id`).

### Receipt actions

| Method | Endpoint | Permission | Response |
|--------|----------|------------|----------|
| GET | `/receipts/{receipt_no}/download/` | Read-only auth | PDF blob |
| POST | `/receipts/{receipt_no}/regenerate/` | Officer | `{ status: string }` |

### Fee Collections (`/fee-collections/`)

**Permission:** `IsCommitteeOfficer | IsAuthenticatedReadOnly`.

```ts
export type FeeType = 'membership' | 'renewal' | 'royalty' | 'other';
export type FeePaymentStatus = 'paid' | 'due' | 'partial';

export interface FeeCollection {
  id: number;
  member: number | null; // FK
  member_name: string | null; // read-only
  fee_type: FeeType;
  amount: string; // decimal string
  amount_paid: string; // decimal string
  payment_status: FeePaymentStatus; // read-only computed
  receipt_no: string | null; // read-only
  description: string;
  created_at: string;
  updated_at: string;
}

export type FeeCollectionInput = Omit<
  FeeCollection,
  'id' | 'member_name' | 'payment_status' | 'receipt_no' | 'created_at' | 'updated_at'
>;
```

**Filters:** `fee_type`, `payment_status`, `member`.  
**Search:** `member__full_name`, `member__citizenship_no`.

---

## 12. Governance API

Base: `/api/v1/governance/`

**Default permission:** `IsCommitteeOfficer | IsMember | IsSubCommitteeMember | IsAuthenticatedReadOnly`.  
Handover records are `IsCommitteeOfficer` only.

### Committee Members (`/committee-members/`)

```ts
export type CommitteePosition =
  | 'chair'
  | 'vice_chair'
  | 'secretary'
  | 'joint_secretary'
  | 'treasurer'
  | 'member';

export type CommitteeMemberStatus = 'active' | 'vacant' | 'removed';

export interface CommitteeMember {
  id: number;
  member: number; // FK to members.Member
  member_name: string; // read-only
  position: CommitteePosition;
  gender: string;
  caste_ethnicity: string;
  term_start: string;
  term_end: string;
  status: CommitteeMemberStatus;
  subcommittees: number[]; // many-to-many FKs
  subcommittee_names: string[]; // read-only display names
  created_at: string;
  updated_at: string;
}

export type CommitteeMemberInput = Omit<
  CommitteeMember,
  'id' | 'member_name' | 'subcommittee_names' | 'created_at' | 'updated_at'
>;
```

**Filters:** `position`, `status`, `term_start`, `term_end`.  
**Search:** `member__full_name`, `position`.

### Quota status action

| Method | Endpoint | Permission | Response |
|--------|----------|------------|----------|
| GET | `/committee-members/quota_status/` | Any authenticated read | `{ active_total, female_count, female_min, female_quota_met, minority_count, minority_min, minority_quota_met }` |

### Elections (`/elections/`)

```ts
export type ElectionStatus = 'in_progress' | 'completed';

export interface Election {
  id: number;
  election_committee_members: string;
  election_date: string;
  status: ElectionStatus;
  candidates: Candidate[]; // nested read-only
  created_at: string;
  updated_at: string;
}

export type ElectionInput = Omit<Election, 'id' | 'candidates' | 'created_at' | 'updated_at'>;
```

**Filters:** `status`, `election_date`.

### Candidates (`/candidates/`)

```ts
export type CandidateResult = 'elected' | 'not_elected';

export interface Candidate {
  id: number;
  election: number; // FK
  member: number; // FK
  member_name: string; // read-only
  position_applied: string;
  votes_received: number;
  result: CandidateResult;
}

export type CandidateInput = Omit<Candidate, 'id' | 'member_name'>;
```

**Filter:** `election`, `result`.

### Subcommittees (`/subcommittees/`)

```ts
export type SubcommitteeName =
  | 'account_fund'
  | 'dispute_resolution'
  | 'infrastructure'
  | 'monitoring'
  | 'livelihood'
  | 'anti_poaching'
  | 'fire_control'
  | 'youth_sports'
  | 'women'
  | 'other';

export interface SubCommittee {
  id: number;
  name: SubcommitteeName;
  tor_description: string;
  created_at: string;
  updated_at: string;
}

export type SubCommitteeInput = Omit<SubCommittee, 'id' | 'created_at' | 'updated_at'>;
```

**Filter:** `name`.

### Oath Records (`/oath-records/`)

```ts
export interface OathRecord {
  id: number;
  committee_member: number; // FK
  committee_member_name: string; // read-only
  oath_date: string;
}

export type OathRecordInput = Omit<OathRecord, 'id' | 'committee_member_name'>;
```

**Filter:** `oath_date`.

### No-Confidence Motions (`/no-confidence-motions/`)

```ts
export type NoConfidenceTarget = 'full_committee' | 'single_officer';
export type AssemblyDecision = 'pending' | 'passed' | 'failed';

export interface NoConfidenceMotion {
  id: number;
  target_type: NoConfidenceTarget;
  target_committee_member: number | null; // FK
  signatures_count: number;
  filed_date: string;
  assembly_decision: AssemblyDecision;
  created_at: string;
  updated_at: string;
}

export type NoConfidenceMotionInput = Omit<
  NoConfidenceMotion,
  'id' | 'created_at' | 'updated_at'
>;
```

**Validation rules:**

- If `target_type = 'single_officer'`: `target_committee_member` is required.
- If `target_type = 'full_committee'`: `target_committee_member` must be blank.

**Filters:** `target_type`, `assembly_decision`.

### Handover Records (`/handover-records/`)

**Permission:** `IsCommitteeOfficer` only.

```ts
export type HandoverStatus = 'pending' | 'completed' | 'escalated';

export interface HandoverRecord {
  id: number;
  outgoing_committee_member: number; // FK
  outgoing_name: string; // read-only
  incoming_committee_member: number | null; // FK
  incoming_name: string | null; // read-only
  cash_amount: string; // decimal string
  assets_summary: string;
  deadline_date: string;
  completed_date: string | null;
  status: HandoverStatus;
  created_at: string;
  updated_at: string;
}

export type HandoverRecordInput = Omit<
  HandoverRecord,
  'id' | 'outgoing_name' | 'incoming_name' | 'created_at' | 'updated_at'
>;
```

**Filters:** `status`, `deadline_date`.

---

## 13. Fund API

Base: `/api/v1/fund/`

**Default permission pattern:** most ViewSets use `IsCommitteeOfficer | IsSubCommitteeMember | IsAuthenticatedReadOnly`; allocation-rules and public-audits use `IsCommitteeOfficer | IsAuthenticatedReadOnly`.

### Fund Allocation Rules (`/allocation-rules/`)

```ts
export interface FundAllocationRule {
  id: number;
  forest_dev_min_percent: string; // decimal string
  poor_targeted_min_percent: string; // decimal string
  effective_from: string;
  created_at: string;
  updated_at: string;
}

export type FundAllocationRuleInput = Omit<
  FundAllocationRule,
  'id' | 'created_at' | 'updated_at'
>;
```

### Bank Accounts (`/bank-accounts/`)

```ts
export interface BankAccount {
  id: number;
  bank_name: string;
  account_number: string;
  signatories: number[]; // JSON list of CommitteeMember IDs
  min_signatures_required: number;
  created_at: string;
  updated_at: string;
}

export type BankAccountInput = Omit<BankAccount, 'id' | 'created_at' | 'updated_at'>;
```

### Cash Transactions (`/cash-transactions/`)

```ts
export type CashTransactionType = 'income' | 'expense';

export interface CashTransaction {
  id: number;
  type: CashTransactionType;
  source_or_purpose: string;
  amount: string; // decimal string
  requires_committee_approval: boolean; // read-only computed
  approved_by: number | null; // FK to core.User
  created_at: string;
  updated_at: string;
}

export type CashTransactionInput = Omit<
  CashTransaction,
  'id' | 'requires_committee_approval' | 'created_at' | 'updated_at'
>;
```

**Validation rule:** if `amount` exceeds the configured chair/treasurer cash approval limit, `approved_by` is required.

**Filters:** `type`, `source_or_purpose`.

### Audits (`/audits/`)

```ts
export type AuditTier = 'internal' | 'external';

export interface Audit {
  id: number;
  fiscal_year: string;
  total_income: string; // decimal string
  audit_tier: AuditTier; // read-only computed
  auditor_name: string;
  findings: string;
  irregularities_recovered: string; // decimal string
  created_at: string;
  updated_at: string;
}

export type AuditInput = Omit<Audit, 'id' | 'audit_tier' | 'created_at' | 'updated_at'>;
```

**Filters:** `fiscal_year`, `audit_tier`.

### Public Audits (`/public-audits/`)

```ts
export interface PublicAudit {
  id: number;
  fiscal_year: string;
  presentation_date: string;
  assembly_approval: boolean;
  created_at: string;
  updated_at: string;
}

export type PublicAuditInput = Omit<PublicAudit, 'id' | 'created_at' | 'updated_at'>;
```

**Filters:** `fiscal_year`, `assembly_approval`.

---

## 14. Livelihood API

Base: `/api/v1/livelihood/`

**Default permission:** `IsCommitteeOfficer | IsSubCommitteeMember | IsMember | IsAuthenticatedReadOnly`.  
Members see only their own household's records.

### Revolving Fund Loans (`/revolving-loans/`)

```ts
export type LoanStatus = 'active' | 'repaid' | 'defaulted';

export interface RevolvingFundLoan {
  id: number;
  household: number; // FK
  household_name: string; // read-only
  amount: string; // decimal string
  issue_date: string;
  repaid_amount: string; // decimal string
  status: LoanStatus;
  created_at: string;
  updated_at: string;
}

export type RevolvingFundLoanInput = Omit<
  RevolvingFundLoan,
  'id' | 'household_name' | 'created_at' | 'updated_at'
>;
```

**Validation rule:** household must have `wealth_class = 'poor'`.

**Filters:** `status`, `issue_date`.

### Livelihood Program Records (`/program-records/`)

```ts
export type LivelihoodProgramType = 'skill_training' | 'livestock' | 'agriculture' | 'other';

export interface LivelihoodProgramRecord {
  id: number;
  household: number; // FK
  household_name: string; // read-only
  program_type: LivelihoodProgramType;
  amount_or_value: string; // decimal string
  program_date: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export type LivelihoodProgramRecordInput = Omit<
  LivelihoodProgramRecord,
  'id' | 'household_name' | 'created_at' | 'updated_at'
>;
```

**Validation rule:** household must have `wealth_class = 'poor'`.

**Filters:** `program_type`, `program_date`.

### Poverty Group Agreements (`/poverty-group-agreements/`)

```ts
export type PovertyAgreementStatus = 'active' | 'ended' | 'terminated_early';

export interface PovertyGroupAgreement {
  id: number;
  subgroup_name: string;
  member_households: number[]; // JSON list of Household IDs
  forest_land_area: string; // decimal string
  term_start: string;
  term_end: string;
  revenue_share_percent: string; // decimal string 0-100
  status: PovertyAgreementStatus;
  created_at: string;
  updated_at: string;
}

export type PovertyGroupAgreementInput = Omit<
  PovertyGroupAgreement,
  'id' | 'created_at' | 'updated_at'
>;
```

**Filter:** `status`.  
**Search:** `subgroup_name`.

---

## 15. Offense API

Base: `/api/v1/offense/`

### Offense Reports (`/reports/`)

**Permission:** `IsCommitteeOfficer | IsMember | IsSubCommitteeMember | IsAuthenticatedReadOnly`.  
Resolve action is `IsCommitteeOfficer` only.

```ts
export type OffenseStatus =
  | 'reported'
  | 'investigating'
  | 'resolved'
  | 'escalated_to_court';

export type OffenseResolution = 'fine_paid' | 'escalated' | 'dismissed';

export interface OffenseReport {
  id: number;
  reported_by: number | null; // FK to members.Member
  accused_name: string;
  offense_type: string;
  description: string;
  report_date: string;
  status: OffenseStatus;
  damage_value: string | null; // decimal string
  fine_amount: string | null; // decimal string
  resolution: OffenseResolution | null;
  informant: number | null; // FK to members.Member
  evidence_count: number; // read-only
  hearings_count: number; // read-only
  created_at: string;
  updated_at: string;
}

export type OffenseReportInput = Omit<
  OffenseReport,
  | 'id'
  | 'evidence_count'
  | 'hearings_count'
  | 'created_at'
  | 'updated_at'
>;
```

**Filters:** `status`, `offense_type`, `report_date`.  
**Search:** `accused_name`, `offense_type`.

### Resolve action

| Method | Endpoint | Body | Permission | Response |
|--------|----------|------|------------|----------|
| POST | `/reports/{id}/resolve/` | `{ informant_id?: number, resolution: OffenseResolution }` | Officer | `OffenseReport` |

### Evidence Items (`/evidence/`)

**Permission:** `IsCommitteeOfficer | IsSubCommitteeMember | IsAuthenticatedReadOnly`.

```ts
export type EvidenceItemType = 'tool' | 'weapon' | 'vehicle' | 'forest_product';

export interface EvidenceItem {
  id: number;
  offense: number; // FK
  item_type: EvidenceItemType;
  description: string;
  confiscated_date: string;
  created_at: string;
}

export type EvidenceItemInput = Omit<EvidenceItem, 'id' | 'created_at'>;
```

**Filters:** `offense`, `item_type`.

### Hearing Records (`/hearings/`)

**Permission:** `IsCommitteeOfficer | IsSubCommitteeMember | IsAuthenticatedReadOnly`.

```ts
export type HearingOutcome = 'admitted' | 'denied';

export interface HearingRecord {
  id: number;
  offense: number; // FK
  accused_statement: string;
  hearing_date: string;
  outcome: HearingOutcome;
  created_at: string;
}

export type HearingRecordInput = Omit<HearingRecord, 'id' | 'created_at'>;
```

**Filters:** `offense`, `hearing_date`.

### Informant Rewards (`/informant-rewards/`)

**Permission:** `IsCommitteeOfficer | IsAuthenticatedReadOnly` (read-only ViewSet).

```ts
export interface InformantReward {
  id: number;
  offense: number; // FK
  informant: number; // FK to members.Member
  reward_amount: string; // decimal string
  paid_date: string;
  created_at: string;
}
```

**Filters:** `offense`, `informant`.

### Patrol Logs (`/patrol-logs/`)

**Permission:** `IsCommitteeOfficer | IsSubCommitteeMember | IsAuthenticatedReadOnly`.

```ts
export interface PatrolLog {
  id: number;
  watcher: number; // FK to members.Member
  watcher_name: string; // read-only
  patrol_date: string;
  notes: string;
  offense: number | null; // FK
  created_at: string;
  updated_at: string;
}

export type PatrolLogInput = Omit<PatrolLog, 'id' | 'watcher_name' | 'created_at' | 'updated_at'>;
```

**Filters:** `watcher`, `patrol_date`.

---

## 16. Reports API

Base: `/api/v1/reports/`

**Permission:** `IsCommitteeOfficer | IsAuthenticatedReadOnly`.

All endpoints are `GET`. Append `?export=pdf` for PDF blob response.

| Endpoint | JSON Response | Notes |
|----------|---------------|-------|
| GET `/tree-count/` | `{ tree_counts: TreeCountReportItem[] }` | Per species/block counts |
| GET `/harvest/` | `{ harvest_summary: HarvestSummaryItem[] }` | Grouped by source_type/status |
| GET `/stock-register/` | `{ stock_register: StockRegisterReportItem[] }` | Current stock positions |
| GET `/sales/` | `{ sales_summary: SalesSummaryItem[] }` | Grouped by buyer_type |
| GET `/visitor-entries/` | `{ visitor_entries: VisitorEntrySummaryItem[] }` | Grouped by visit_purpose |
| GET `/fund-audit/` | `{ total_income, total_expense, net, audits: AuditReportItem[] }` | |
| GET `/governance/` | `{ committee_total, female_members, elections_held }` | |
| GET `/livelihood/` | `{ loans: LoanSummaryItem[], programs: ProgramSummaryItem[] }` | |
| GET `/offense/` | `{ by_status: OffenseStatusItem[], total_fines, total_rewards }` | |
| GET `/annual-dfo/` | `{ total_members, total_households, total_tree_counts, ... }` | Cross-app annual summary |

```ts
export interface TreeCountReportItem {
  species__species_name: string;
  block__block_name: string | null;
  total_count: number;
  harvested_count: number;
  remaining_count: number;
}

export interface HarvestSummaryItem {
  source_type: HarvestSourceType;
  status: HarvestStatus;
  count: number;
  total_quantity: string;
}

export interface StockRegisterReportItem {
  species__species_name: string;
  grade: string;
  quantity_available: string;
}

export interface SalesSummaryItem {
  buyer_type: InventoryBuyerType;
  count: number;
  total_quantity: string;
  total_amount: string;
}

export interface VisitorEntrySummaryItem {
  visit_purpose: VisitPurpose;
  count: number;
  total_amount: string;
}

export interface FundAuditReport {
  total_income: string;
  total_expense: string;
  net: string;
  audits: {
    id: number;
    fiscal_year: string;
    audit_tier: AuditTier;
    auditor_name: string;
  }[];
}

export interface GovernanceReport {
  committee_total: number;
  female_members: number;
  elections_held: number;
}

export interface LivelihoodReport {
  loans: { status: LoanStatus; count: number; total_amount: string }[];
  programs: { program_type: LivelihoodProgramType; count: number; total_value: string }[];
}

export interface OffenseReportSummary {
  by_status: { status: OffenseStatus; count: number }[];
  total_fines: string;
  total_rewards: string;
}

export interface AnnualDfoReport {
  total_members: number;
  total_households: number;
  total_tree_counts: number;
  total_harvest_requests: number;
  total_sales: number;
  total_visitor_entries: number;
  total_official_guests: number;
  total_income: string;
  total_expense: string;
}
```

---

## 17. Step-by-Step Integration

### 17.1 Install dependencies

```bash
npm install axios @tanstack/react-query zustand zod sonner date-fns
npm install -D @types/node
```

### 17.2 Create the API client

Create `src/lib/api/client.ts`:

```ts
import axios, { InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/stores/auth-store';

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().token;
  if (token && config.headers) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
```

### 17.3 Create typed API modules

Example: `src/lib/api/members.ts`

```ts
import { apiClient } from './client';
import type {
  Household,
  Member,
  MemberListItem,
  MembershipRenewal,
  PaginatedResponse,
} from '@/types/api';

export const householdsApi = {
  list: (params?: Record<string, unknown>) =>
    apiClient.get<PaginatedResponse<Household>>('/v1/members/households/', { params }),
  get: (id: number | string) =>
    apiClient.get<Household>(`/v1/members/households/${id}/`),
  create: (data: Omit<Household, 'id' | 'entry_fee_due' | 'created_at' | 'updated_at'>) =>
    apiClient.post<Household>('/v1/members/households/', data),
  update: (id: number | string, data: Partial<Household>) =>
    apiClient.patch<Household>(`/v1/members/households/${id}/`, data),
  delete: (id: number | string) =>
    apiClient.delete(`/v1/members/households/${id}/`),
};

export const membersApi = {
  list: (params?: Record<string, unknown>) =>
    apiClient.get<PaginatedResponse<MemberListItem>>('/v1/members/members/', { params }),
  get: (id: number | string) =>
    apiClient.get<Member>(`/v1/members/members/${id}/`),
  create: (data: Omit<Member, 'id' | 'household_name' | 'user_email' | 'created_at' | 'updated_at'>) =>
    apiClient.post<Member>('/v1/members/members/', data),
  update: (id: number | string, data: Partial<Member>) =>
    apiClient.patch<Member>(`/v1/members/members/${id}/`, data),
  delete: (id: number | string) =>
    apiClient.delete(`/v1/members/members/${id}/`),
};

export const renewalsApi = {
  list: (params?: Record<string, unknown>) =>
    apiClient.get<PaginatedResponse<MembershipRenewal>>(
      '/v1/members/membership-renewals/',
      { params }
    ),
};
```

### 17.4 Add React Query hooks

Example: `src/hooks/use-households.ts`

```ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { householdsApi } from '@/lib/api/members';
import { queryKeys } from '@/lib/query-keys';
import type { Household, PaginatedResponse } from '@/types/api';

export function useHouseholds(filters: Record<string, unknown> = {}) {
  return useQuery<PaginatedResponse<Household>>({
    queryKey: queryKeys.households.list(filters),
    queryFn: async () => (await householdsApi.list(filters)).data,
  });
}

export function useCreateHousehold() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: householdsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['households', 'list'] });
    },
  });
}
```

### 17.5 Wire forms with Zod

Use the schemas in [Section 18](#18-zod-schemas) with `react-hook-form`:

```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { householdSchema, HouseholdInput } from '@/schemas/household.schema';

const form = useForm<HouseholdInput>({
  resolver: zodResolver(householdSchema),
  defaultValues: { status: 'active', wealth_class: 'poor' },
});
```

### 17.6 Handle permissions in UI

See [Section 19](#19-permission-guards). Use the `useRole` hook to hide write buttons for non-officers.

---

## 18. Zod Schemas

Create `src/schemas/` and mirror the backend validation.

```ts
// src/schemas/household.schema.ts
import { z } from 'zod';

export const householdSchema = z.object({
  household_head_name: z.string().min(1, 'Head name is required'),
  tole: z.string().default(''),
  wealth_class: z.enum(['rich', 'medium', 'poor']),
  population_male: z.number().int().min(0).default(0),
  population_female: z.number().int().min(0).default(0),
  livestock_cattle: z.number().int().min(0).default(0),
  livestock_buffalo: z.number().int().min(0).default(0),
  livestock_goat: z.number().int().min(0).default(0),
  education_level: z.enum(['illiterate', 'basic', 'secondary_plus']).optional(),
  occupation: z.string().default(''),
  caste_ethnicity: z.string().default(''),
  registration_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Use YYYY-MM-DD'),
  entry_fee_type: z.enum(['new_household', 'split_household']),
  status: z.enum(['active', 'inactive']).default('active'),
});

export type HouseholdInput = z.infer<typeof householdSchema>;
```

```ts
// src/schemas/member.schema.ts
import { z } from 'zod';

export const memberSchema = z.object({
  household: z.number({ required_error: 'Household is required' }),
  user: z.number().nullable().optional(),
  full_name: z.string().min(1, 'Full name is required'),
  citizenship_no: z.string().min(1, 'Citizenship number is required'),
  membership_type: z.enum(['general', 'lifetime', 'institutional', 'special', 'other']),
  membership_status: z.enum(['active', 'inactive', 'cancelled']).default('active'),
  date_joined: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
});

export type MemberInput = z.infer<typeof memberSchema>;
```

```ts
// src/schemas/harvest.schema.ts
import { z } from 'zod';

export const harvestRequestSchema = z
  .object({
    source_type: z.enum(['member_requested', 'forest_initiated']),
    member: z.number().nullable().optional(),
    operation_name: z.string().default(''),
    species: z.number({ required_error: 'Species is required' }),
    quantity: z.string().min(1, 'Quantity is required'),
    requested_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
    notes: z.string().default(''),
  })
  .refine(
    (data) =>
      data.source_type === 'member_requested'
        ? Boolean(data.member) && data.operation_name === ''
        : data.member === null || data.member === undefined,
    {
      message: 'Invalid member/operation combination for source type',
      path: ['member'],
    }
  );

export type HarvestRequestInput = z.infer<typeof harvestRequestSchema>;
```

---

## 19. Permission Guards

Create `src/hooks/use-role.ts`:

```ts
import { useAuth } from '@/hooks/use-auth';

export function useRole() {
  const { user } = useAuth();
  const role = user?.role;

  return {
    role,
    isAdmin: role === 'admin',
    isCommitteeOfficer: role === 'committee_officer' || role === 'admin',
    isMember: role === 'member',
    isSubCommittee: role === 'sub_committee_member',
    isDfoViewer: role === 'dfo_viewer',
    canWrite: role === 'committee_officer' || role === 'admin',
    canReadAll:
      role === 'committee_officer' ||
      role === 'admin' ||
      role === 'dfo_viewer',
  };
}
```

Create `src/components/auth/permission-guard.tsx`:

```tsx
'use client';
import { useRole } from '@/hooks/use-role';

interface PermissionGuardProps {
  children: React.ReactNode;
  required: 'write' | 'readAll' | 'committeeOfficer';
  fallback?: React.ReactNode;
}

export function PermissionGuard({
  children,
  required,
  fallback = null,
}: PermissionGuardProps) {
  const role = useRole();

  const allowed =
    (required === 'write' && role.canWrite) ||
    (required === 'readAll' && role.canReadAll) ||
    (required === 'committeeOfficer' && role.isCommitteeOfficer);

  return allowed ? <>{children}</> : <>{fallback}</>;
}
```

Usage in a page:

```tsx
<PermissionGuard required="write">
  <Button onClick={openCreateModal}>Add Member</Button>
</PermissionGuard>
```

---

## 20. Error Handling

DRF returns these shapes:

```ts
// Validation error (400)
{ "field_name": ["This field is required."], "non_field_errors": ["..."] }

// Generic error
{ "detail": "Authentication credentials were not provided." }
```

Create a normalized error class:

```ts
// src/lib/errors.ts
import { AxiosError } from 'axios';

export class ApiError extends Error {
  status: number;
  fieldErrors: Record<string, string[]>;

  constructor(
    message: string,
    status: number,
    fieldErrors: Record<string, string[]> = {}
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.fieldErrors = fieldErrors;
  }

  static fromAxios(error: AxiosError<unknown>): ApiError {
    const status = error.response?.status ?? 0;
    const data = error.response?.data;

    if (typeof data === 'string') {
      return new ApiError(data || error.message, status);
    }

    if (data && typeof data === 'object') {
      const obj = data as Record<string, unknown>;
      const detail = obj.detail;
      const message = Array.isArray(detail)
        ? detail.join(' ')
        : typeof detail === 'string'
        ? detail
        : 'Something went wrong';

      const fieldErrors: Record<string, string[]> = {};
      for (const [key, value] of Object.entries(obj)) {
        if (key === 'detail') continue;
        fieldErrors[key] = Array.isArray(value)
          ? value.map(String)
          : [String(value)];
      }
      return new ApiError(message, status, fieldErrors);
    }

    return new ApiError(error.message || 'Network error', status);
  }
}
```

Map field errors to React Hook Form:

```ts
if (error instanceof ApiError) {
  Object.entries(error.fieldErrors).forEach(([field, messages]) => {
    form.setError(field as keyof FormType, {
      type: 'manual',
      message: messages.join(', '),
    });
  });
}
```

---

## Summary Checklist

Before you call an endpoint from the frontend:

1. **Check the permission class** — hide UI actions users cannot perform.
2. **Use the correct TypeScript type** for request body and response.
3. **Respect read-only fields** — do not send `id`, `*_name`, `created_at`, `updated_at`, or computed fields.
4. **Use ISO date strings** (`YYYY-MM-DD`) for all date fields.
5. **Use decimal strings** for money / quantity fields (DRF serializes `DecimalField` as string).
6. **Add filters/search** using the documented query parameters.
7. **Handle pagination** with `limit` / `offset`.
8. **Validate with Zod** before sending to the backend.
9. **Map backend errors** to form fields and toast messages.
10. **Use `?export=pdf`** for report/receipt PDF downloads.

---

**End of document.**
