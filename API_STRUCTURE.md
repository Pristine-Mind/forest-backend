# Forest Backend API Structure Documentation

**Base URL:** `/api/v1/`
**Authentication:** Token-based (user login returns auth token)
**Format:** JSON

---

## Table of Contents
1. [Core Module](#core-module)
2. [Members Module](#members-module)
3. [Forest Module](#forest-module)
4. [Harvest Module](#harvest-module)
5. [Inventory Module](#inventory-module)
6. [Visitors Module](#visitors-module)
7. [Billing Module](#billing-module)
8. [Governance Module](#governance-module)
9. [Fund Module](#fund-module)
10. [Livelihood Module](#livelihood-module)
11. [Offense Module](#offense-module)
12. [Reports Module](#reports-module)

---

## CORE MODULE
**Endpoint Base:** `/api/v1/core/`

### Authentication Endpoints

#### 1. **Login** `POST /auth/login/`
- **Description:** Authenticate user and receive auth token
- **Request Body:**
  - `email` (string, required)
  - `password` (string, required, min 8 chars)
- **Response:** 
  - `token` (string) - Authentication token for API requests
  - `user` (object) - User details
- **Permissions:** AllowAny

#### 2. **Logout** `POST /auth/logout/`
- **Description:** Invalidate user's auth token
- **Response:** Success message
- **Permissions:** IsAuthenticated

#### 3. **Get Current User** `GET /users/me/`
- **Description:** Get authenticated user's profile
- **Response:** User object with email, name, role, is_active
- **Permissions:** IsAuthenticated

### User Management

#### 4. **List Users** `GET /users/`
- **Description:** List all users (committee officers only)
- **Querystring Filters:**
  - `search=` - Search by email, first_name, last_name
- **Response:** Array of user objects
- **Permissions:** IsCommitteeOfficer

#### 5. **Create User** `POST /users/`
- **Description:** Create new user (committee officers only)
- **Request Body:**
  - `email` (string, required, unique)
  - `first_name` (string)
  - `last_name` (string)
  - `role` (choice: committee_officer | member | sub_committee_member | dfo_viewer | admin)
  - `password` (string, required, min 8 chars)
  - `is_active` (boolean)
- **Response:** Created user object with ID
- **Permissions:** IsCommitteeOfficer

#### 6. **Get User** `GET /users/{id}/`
- **Response:** User object
- **Permissions:** IsCommitteeOfficer

#### 7. **Update User** `PATCH /users/{id}/`
- **Editable Fields:** email, first_name, last_name, role, is_active
- **Permissions:** IsCommitteeOfficer

#### 8. **Delete User** `DELETE /users/{id}/`
- **Permissions:** IsCommitteeOfficer

### System Configuration

#### 9. **Get System Config** `GET /system-config/1/`
- **Description:** Retrieve singleton system configuration
- **Returns:** Current configuration values
- **Accessible Fields:**
  - Membership fees: `new_household_entry_fee`, `split_household_entry_fee`, `renewal_fee_on_time`, `renewal_fee_overdue_3yr`, `renewal_fee_overdue_5yr`, `renewal_fee_overdue_5yr_plus`, `membership_cancellation_years`
  - Fund allocation: `forest_dev_min_percent`, `poor_targeted_min_percent`
  - Cash limits: `cash_chair_approval_limit`, `cash_treasurer_approval_limit`
  - Audit: `audit_external_threshold`
  - Other: `informant_reward_percent`, `no_confidence_signature_percent`, `handover_deadline_days`, `min_female_committee_members`, `current_fiscal_year`
- **Permissions:** IsAuthenticated (read), IsCommitteeOfficer (write)

#### 10. **Update System Config** `PATCH /system-config/1/`
- **Description:** Update system configuration
- **Permissions:** IsCommitteeOfficer

---

## MEMBERS MODULE
**Endpoint Base:** `/api/v1/members/`

### User Roles & Permissions:
- **Committee Officers:** Full access
- **Members:** Can only see their own household and profile
- **Sub-committee Members:** Limited view
- **DFO Viewers:** Read-only

### Household Management

#### 1. **List Households** `GET /households/`
- **Description:** Retrieve household records
- **Querystring Filters:**
  - `wealth_class=` (rich | medium | poor)
  - `tole=` (filter by location)
  - `status=` (active | inactive)
  - `search=` - Search by household_head_name, tole
- **Response Fields per Record:**
  - `id`, `household_head_name`, `tole`, `wealth_class`
  - `population_male`, `population_female`
  - `livestock_cattle`, `livestock_buffalo`, `livestock_goat`
  - `education_level`, `occupation`, `caste_ethnicity`
  - `registration_date`, `entry_fee_type`, `entry_fee_due` (calculated), `status`
  - `created_at`, `updated_at`
- **Permissions:** IsCommitteeOfficer | IsMember | IsSubCommitteeMember | IsDFOViewer

#### 2. **Create Household** `POST /households/`
- **Request Body:**
  - `household_head_name` (string, required)
  - `tole` (string)
  - `wealth_class` (choice: rich | medium | poor, required)
  - `population_male` (integer, default 0)
  - `population_female` (integer, default 0)
  - `livestock_cattle`, `livestock_buffalo`, `livestock_goat` (integer, default 0)
  - `education_level` (choice: illiterate | basic | secondary_plus)
  - `occupation` (string)
  - `caste_ethnicity` (string)
  - `registration_date` (date, required)
  - `entry_fee_type` (choice: new_household | split_household)
  - `status` (choice: active | inactive)
- **Response:** Created household object with `entry_fee_due` calculated
- **Permissions:** IsCommitteeOfficer

#### 3. **Get Household** `GET /households/{id}/`

#### 4. **Update Household** `PATCH /households/{id}/`

#### 5. **Delete Household** `DELETE /households/{id}/`

### Member Management

#### 6. **List Members** `GET /members/`
- **Description:** Retrieve member records
- **Querystring Filters:**
  - `membership_type=` (general | lifetime | institutional | special | other)
  - `membership_status=` (active | inactive | cancelled)
  - `household__wealth_class=` (rich | medium | poor)
  - `search=` - Search by full_name, citizenship_no
- **Response Fields:**
  - `id`, `household`, `household_name` (read-only)
  - `user_email` (read-only, linked user email)
  - `full_name`, `citizenship_no`, `membership_type`, `membership_status`
  - `date_joined`, `created_at`, `updated_at`
- **List View (Simpler):** Returns only id, full_name, citizenship_no, membership_status, household_name, membership_type, date_joined
- **Permissions:** IsCommitteeOfficer | IsMember | IsSubCommitteeMember | IsDFOViewer

#### 7. **Create Member** `POST /members/`
- **Request Body:**
  - `household` (integer, foreign key to Household, required)
  - `full_name` (string, required)
  - `citizenship_no` (string, required, unique)
  - `membership_type` (choice, default: general)
  - `membership_status` (choice, default: active)
  - `date_joined` (date, required)
  - `user` (optional, link to User)
- **Response:** Created member object
- **Permissions:** IsCommitteeOfficer

#### 8. **Get Member** `GET /members/{id}/`

#### 9. **Update Member** `PATCH /members/{id}/`

#### 10. **Delete Member** `DELETE /members/{id}/`

### Membership Renewal

#### 11. **List Membership Renewals** `GET /membership-renewals/`
- **Description:** Retrieve renewal payment records
- **Querystring Filters:**
  - `fiscal_year=` (e.g., "2082/83")
  - `fee_tier=` (on_time | overdue_3yr | overdue_5yr | overdue_5yr_plus)
  - `search=` - Search by member__full_name, member__citizenship_no
- **Response Fields:**
  - `id`, `member`, `member_name` (read-only)
  - `fiscal_year`, `fee_tier`, `fee_charged`, `paid_date`
  - `created_at`, `updated_at`
- **Permissions:** IsCommitteeOfficer

#### 12. **Create Membership Renewal** `POST /membership-renewals/`
- **Request Body:**
  - `member` (integer, required)
  - `fiscal_year` (string, required)
  - `paid_date` (date, required)
- **Note:** `fee_tier` and `fee_charged` calculated based on last renewal and system config
- **Response:** Created renewal object
- **Permissions:** IsCommitteeOfficer

#### 13. **Get/Update/Delete Membership Renewal** `GET|PATCH|DELETE /membership-renewals/{id}/`

---

## FOREST MODULE
**Endpoint Base:** `/api/v1/forest/`

### Forest Blocks

#### 1. **List Forest Blocks** `GET /blocks/`
- **Querystring Filters:**
  - `block_name=` - Search by exact name
  - `search=` - Search by block_name
- **Response Fields:**
  - `id`, `block_name`, `area_hectares`, `created_at`, `updated_at`
- **Permissions:** IsCommitteeOfficer | IsAuthenticatedReadOnly

#### 2. **Create/Read/Update/Delete Forest Block** `POST|GET|PATCH|DELETE /blocks/`

#### 3. **Create Block** `POST /blocks/`
- **Request Body:**
  - `block_name` (string, required)
  - `area_hectares` (decimal, required, minimum 0)

### Species Management

#### 4. **List Tree Species** `GET /species/`
- **Querystring Filters:**
  - `search=` - Search by species_name, scientific_name, local_name
- **Response Fields:**
  - `id`, `species_name`, `scientific_name`, `local_name`, `created_at`, `updated_at`
- **Permissions:** IsCommitteeOfficer | IsAuthenticatedReadOnly

#### 5. **Create/Read/Update/Delete Species** `POST|GET|PATCH|DELETE /species/{id}/`
- **Request Body:**
  - `species_name` (string, required, unique)
  - `scientific_name` (string)
  - `local_name` (string)

#### 6. **List Wildlife Species** `GET /wildlife-species/`
- **Same as species - returns:** `id`, `species_name`, `scientific_name`, `local_name`

#### 7. **Create/Read/Update/Delete Wildlife Species** `POST|GET|PATCH|DELETE /wildlife-species/{id}/`

### Operational Plans

#### 8. **List Operational Plans** `GET /operational-plans/`
- **Querystring Filters:**
  - `valid_from=` (date filter)
  - `valid_to=` (date filter)
- **Response Fields:**
  - `id`, `valid_from`, `valid_to`, `approved_harvest_limit`, `description`, `created_at`, `updated_at`
- **Permissions:** IsCommitteeOfficer | IsAuthenticatedReadOnly

#### 9. **Create/Read/Update/Delete Operational Plan** `POST|GET|PATCH|DELETE /operational-plans/{id}/`
- **Request Body:**
  - `valid_from` (date, required)
  - `valid_to` (date, required)
  - `approved_harvest_limit` (decimal, required, minimum 0)
  - `description` (text)

### Tree Count Register

#### 10. **List Tree Records** `GET /tree-counts/`
- **Querystring Filters:**
  - `block=` (block ID)
  - `operational_plan=` (operational plan ID)
  - `species=` (species ID)
  - `tree_class=` (i | ii | iii)
  - `is_harvestable=` (true | false)
  - `is_active=` (true | false)
  - `plot_number=` (integer)
  - `search=` - Search by block__block_name, species__species_name, notes
  - `ordering=` - Sort by: plot_number, tree_number, girth_cm, height_m, total_volume_cubic_m, created_at
- **Response Fields (Extensive):**
  - **Relationships:** `id`, `block`, `block_name` (read-only), `operational_plan`, `species`, `species_name` (read-only)
  - **Plot Info:** `plot_number`, `tree_number`
  - **Measurements:** `girth_cm`, `height_m`, `tree_class`, `tree_class_display` (read-only)
  - **Auto-Calculated Volumes (read-only):**
    - `basal_area_sqm`, `stem_volume_cubic_m`, `r_factor`
    - `branch_volume_cubic_m`, `total_volume_cubic_m`, `r_less_than_10`
    - `volume_less_than_10_cubic_m`, `gross_volume_cubic_m`, `net_volume_cubic_m`, `fuelwood_volume_cubic_m`
  - **Metadata:** `survey_date`, `is_harvestable`, `is_active`, `notes`, `created_at`, `updated_at`
- **Permissions:** IsCommitteeOfficer | IsAuthenticatedReadOnly

#### 11. **Create Tree Record** `POST /tree-counts/`
- **Request Body:**
  - `block` (integer, required)
  - `operational_plan` (integer, optional)
  - `species` (integer, required)
  - `plot_number` (integer, required)
  - `tree_number` (integer, required)
  - `girth_cm` (decimal, 0-500, required) - Measured in cm
  - `height_m` (decimal, 0-100, required) - Measured in meters
  - `tree_class` (choice: i | ii | iii, required)
  - `survey_date` (date)
  - `is_harvestable` (boolean, default: true)
  - `is_active` (boolean, default: true)
  - `notes` (text)
- **Response:** Calculated volumes auto-filled
- **Validation:** Unique constraint on (block, plot_number, tree_number)

#### 12. **Get/Update/Delete Tree Record** `GET|PATCH|DELETE /tree-counts/{id}/`

#### 13. **Plot Summary** `GET /tree-counts/plot-summary/?block_id=X&section_id=Y&plot_number=Z`
- **Description:** Get aggregated data for a specific plot
- **Response:**
  - `block_id`, `section_id`, `plot_number`
  - `total_trees`, `total_volume`, `total_net_volume`, `total_fuelwood`
  - `species_count`, `average_height`, `average_girth`
  - `trees` - Array of tree records

#### 14. **Section Summary** `GET /tree-counts/section-summary/?block_id=X&section_id=Y`
- **Response:** Aggregated data for all plots in section

#### 15. **Block Summary** `GET /tree-counts/block-summary/?block_id=X&operational_plan_id=Y(optional)`
- **Response:** Complete block statistics

### Tree Count History

#### 16. **List Tree Count History** `GET /tree-count-history/`
- **Description:** Track changes to tree records (harvest, damage, etc.)
- **Response Fields:**
  - `id`, `record`, `record_details` (species, block, plot, tree_number)
  - `change_amount`, `reference_harvest`, `change_date`, `note`, `created_at`

### Harvest Logs

#### 17. **List Harvest Logs** `GET /harvest-logs/`
- **Response Fields:**
  - `id`, `tree_record`, `tree_details` (read-only)
  - `harvest_date`, `harvest_quantity_cubic_m`
  - `reference_harvest_request`, `notes`, `created_at`, `updated_at`

#### 18. **Create Harvest Log** `POST /harvest-logs/`
- **Request Body:**
  - `tree_record` (integer, required)
  - `harvest_date` (date, required)
  - `harvest_quantity_cubic_m` (decimal, required)
  - `reference_harvest_request` (integer, optional)
  - `notes` (text)

### Pole Count Register

#### 19. **List Pole Counts** `GET /pole-counts/`
- **Response Fields:** Similar structure to tree counts but for smaller diameter logs

#### 20. **Create/Read/Update/Delete Pole Record** `POST|GET|PATCH|DELETE /pole-counts/{id}/`

---

## HARVEST MODULE
**Endpoint Base:** `/api/v1/harvest/`

### Harvest Requests

#### 1. **List Harvest Requests** `GET /requests/`
- **Querystring Filters:**
  - `source_type=` (member_requested | forest_initiated)
  - `status=` (pending | approved | rejected)
  - `species=` (species ID)
  - `requested_date=` (date filter)
  - `search=` - Search by member__full_name, species__species_name, operation_name
- **Response Fields:**
  - `id`, `source_type`, `member`, `member_name` (read-only)
  - `operation_name`, `species`, `species_name` (read-only)
  - `quantity`, `status`, `requested_date`
  - `approved_by`, `approved_by_name` (read-only), `notes`
  - `created_at`, `updated_at`
- **Permissions:** IsCommitteeOfficer | IsMember | IsAuthenticatedReadOnly

#### 2. **Create Harvest Request** `POST /requests/`
- **Request Body:**
  - `source_type` (choice: member_requested | forest_initiated, required)
  - If `source_type == member_requested`:
    - `member` (required, will be auto-filled with current user's member profile if IsMember)
    - `operation_name` (must be blank)
  - If `source_type == forest_initiated`:
    - `operation_name` (string, required)
    - `member` (must be blank)
  - `species` (integer, required)
  - `quantity` (decimal, required, minimum 0.01)
  - `requested_date` (date, required)
  - `notes` (text)
- **Validation:** 
  - Member must be ACTIVE for member-requested harvests
  - Forest-initiated needs operation name instead of member
- **Response:** Created request object with status=pending

#### 3. **Get Harvest Request** `GET /requests/{id}/`

#### 4. **Update Harvest Request** `PATCH /requests/{id}/`
- **Note:** Regular users cannot change status. Only committee can approve/reject.

#### 5. **Delete Harvest Request** `DELETE /requests/{id}/`

#### 6. **Approve Harvest Request** `POST /requests/{id}/approve/`
- **Description:** Committee officers approve a pending harvest
- **Permissions:** IsCommitteeOfficer
- **Response:** Updated request with status=approved

#### 7. **Reject Harvest Request** `POST /requests/{id}/reject/`
- **Description:** Committee officers reject a pending harvest
- **Request Body:**
  - `notes` (string, required - reason for rejection)
- **Permissions:** IsCommitteeOfficer
- **Response:** Updated request with status=rejected

---

## INVENTORY MODULE
**Endpoint Base:** `/api/v1/inventory/`

### Stock Ledger

#### 1. **List Stock Ledgers** `GET /ledgers/`
- **Querystring Filters:**
  - `species=` (species ID)
  - `grade=` (wood grade)
  - `search=` - Search by species__species_name, grade
- **Response Fields:**
  - `id`, `species`, `species_name` (read-only)
  - `grade`, `quantity_available` (read-only, calculated from transactions)
  - `created_at`, `updated_at`
- **Permissions:** IsCommitteeOfficer | IsAuthenticatedReadOnly

#### 2. **Create Stock Ledger** `POST /ledgers/`
- **Request Body:**
  - `species` (integer, required)
  - `grade` (string, required)
- **Validation:** Unique constraint on (species, grade)
- **Response:** Created ledger with quantity_available = 0

#### 3. **Get/Update/Delete Stock Ledger** `GET|PATCH|DELETE /ledgers/{id}/`

### Stock Transactions

#### 4. **List Stock Transactions** `GET /stock-transactions/`
- **Querystring Filters:**
  - `stock=` (stock ledger ID)
  - `transaction_type=` (in | out)
  - `reference_type=` (harvest | sale | adjustment)
- **Response Fields:**
  - `id`, `stock`, `transaction_type`, `quantity`
  - `reference_type`, `reference_id`, `note`
  - `created_at`
- **Permissions:** IsCommitteeOfficer | IsAuthenticatedReadOnly

#### 5. **Create Stock Transaction** `POST /stock-transactions/`
- **Request Body:**
  - `stock` (integer, required)
  - `transaction_type` (choice: in | out, required)
  - `quantity` (decimal, required, minimum 0.01)
  - `reference_type` (choice: harvest | sale | adjustment, required)
  - `reference_id` (integer, required)
  - `note` (text)
- **Response:** Created transaction

#### 6. **Record Adjustment** `POST /stock-transactions/record_adjustment/`
- **Description:** Convenient endpoint for inventory adjustments
- **Permissions:** IsCommitteeOfficer

### Price Rates

#### 7. **List Price Rates** `GET /price-rates/`
- **Querystring Filters:**
  - `species=` (species ID)
  - `grade=` (wood grade)
  - `buyer_type=` (member | outsider)
- **Response Fields:**
  - `id`, `species`, `species_name` (read-only)
  - `grade`, `buyer_type`, `rate_per_unit`
  - `effective_from`, `created_at`, `updated_at`
- **Permissions:** IsCommitteeOfficer | IsAuthenticatedReadOnly

#### 8. **Create Price Rate** `POST /price-rates/`
- **Request Body:**
  - `species` (integer, required)
  - `grade` (string, required)
  - `buyer_type` (choice: member | outsider, required)
  - `rate_per_unit` (decimal, required, minimum 0.01)
  - `effective_from` (date, required)
- **Validation:** Unique on (species, grade, buyer_type, effective_from)
- **Response:** Created rate

#### 9. **Get/Update/Delete Price Rate** `GET|PATCH|DELETE /price-rates/{id}/`

### Sales

#### 10. **List Sales** `GET /sales/`
- **Querystring Filters:**
  - `buyer_type=` (member | outsider)
  - `species=` (species ID)
  - `grade=` (wood grade)
  - `payment_status=` (paid | due | partial)
  - `search=` - Search by buyer_name, member__full_name
- **Response Fields:**
  - `id`, `buyer_name`, `buyer_type`
  - `member`, `member_name` (read-only, null for outsiders)
  - `species`, `species_name` (read-only)
  - `grade`, `quantity`, `rate_applied`, `total_amount` (read-only)
  - `payment_status`, `receipt_no`, `audit_note`
  - `created_at`, `updated_at`
- **Permissions:** IsCommitteeOfficer | IsAuthenticatedReadOnly

#### 11. **Create Sale** `POST /sales/`
- **Request Body:**
  - `buyer_name` (string, required)
  - `buyer_type` (choice: member | outsider, required)
  - If `buyer_type == member`: `member` (integer, required)
  - If `buyer_type == outsider`: `member` (must be null)
  - `species` (integer, required)
  - `grade` (string, required)
  - `quantity` (decimal, required, minimum 0.01)
  - `rate_applied` (decimal, required, minimum 0.01 - auto-filled from price rate but editable)
  - `audit_note` (text, required if rate_applied differs from current price)
- **Response:** Created sale with `total_amount` calculated as quantity × rate_applied
- **Note:** `total_amount` and `payment_status` are read-only

#### 12. **Record Sale** `POST /sales/record/`
- **Description:** Convenience endpoint that links sale to visitor/fee collection
- **Permissions:** IsCommitteeOfficer

#### 13. **Get/Update/Delete Sale** `GET|PATCH|DELETE /sales/{id}/`

---

## VISITORS MODULE
**Endpoint Base:** `/api/v1/visitors/`

### Visitor Fee Rates

#### 1. **List Fee Rates** `GET /fee-rates/`
- **Response Fields:**
  - `id`, `visit_purpose` (general_visit | study_research)
  - `fee_per_visitor_per_day`, `created_at`, `updated_at`
- **Permissions:** IsCommitteeOfficer | IsAuthenticatedReadOnly

#### 2. **Create/Update/Delete Fee Rate** `POST|PATCH|DELETE /fee-rates/{id}/`
- **Request Body:**
  - `visit_purpose` (choice: general_visit | study_research, required, unique)
  - `fee_per_visitor_per_day` (decimal, required, minimum 0)

### Visitor Entries

#### 3. **List Visitor Entries** `GET /entries/`
- **Querystring Filters:**
  - `entry_date=` (date filter)
  - `visit_purpose=` (general_visit | study_research)
  - `fee_waived=` (true | false)
- **Response Fields:**
  - `id`, `entry_date`, `visit_purpose`
  - `visitor_count`, `days`
  - `fee_waived`, `total_amount` (read-only)
  - `receipt_no` (read-only), `created_at`, `updated_at`
- **Permissions:** IsCommitteeOfficer | IsAuthenticatedReadOnly

#### 4. **Create Visitor Entry** `POST /entries/`
- **Request Body:**
  - `entry_date` (date, required)
  - `visit_purpose` (choice: general_visit | study_research, required)
  - `visitor_count` (integer, required, minimum 1)
  - `days` (integer, required, minimum 1)
  - `fee_waived` (boolean, default: false)
- **Auto-Calculation:**
  - If `fee_waived == true`: `total_amount = 0`
  - Else: `total_amount = visitor_count × days × fee_per_visitor_per_day`
- **Response:** Created entry with calculated `total_amount`

#### 5. **Get/Update/Delete Visitor Entry** `GET|PATCH|DELETE /entries/{id}/`

#### 6. **Log and Collect** `POST /entries/log_and_collect/`
- **Description:** Convenience endpoint to create visitor entry and link receipt in one call
- **Permissions:** IsCommitteeOfficer

### Official Guest Log

#### 7. **List Official Guests** `GET /official-guests/`
- **Querystring Filters:**
  - `visit_start_date=` (date filter)
  - `visit_end_date=` (date filter)
  - `search=` - Search by visitor_name, designation
- **Response Fields:**
  - `id`, `visitor_name`, `designation`
  - `visit_start_date`, `visit_end_date`
  - `comments_or_guidance`, `created_at`, `updated_at`
- **Permissions:** IsCommitteeOfficer | IsAuthenticatedReadOnly

#### 8. **Create/Read/Update/Delete Official Guest** `POST|GET|PATCH|DELETE /official-guests/{id}/`
- **Request Body:**
  - `visitor_name` (string, required)
  - `designation` (string)
  - `visit_start_date` (date, required)
  - `visit_end_date` (date, required)
  - `comments_or_guidance` (text)

---

## BILLING MODULE
**Endpoint Base:** `/api/v1/billing/`

### Receipts

#### 1. **List Receipts** `GET /receipts/`
- **Querystring Filters:**
  - `reference_type=` (sale | fee_collection | visitor_entry)
  - `issued_date=` (date filter)
  - `search=` - Search by receipt_no
- **Response Fields:**
  - `receipt_no` (string, primary key)
  - `reference_type`, `reference_id`
  - `amount`, `issued_date`
  - `issued_by`, `pdf_file`, `created_at`
- **Permissions:** IsCommitteeOfficer | IsAuthenticatedReadOnly

#### 2. **Get Receipt** `GET /receipts/{receipt_no}/`

#### 3. **Download Receipt PDF** `GET /receipts/{receipt_no}/download/`
- **Description:** Download generated PDF file for receipt
- **Response:** PDF file (application/pdf)

#### 4. **Regenerate PDF** `POST /receipts/{receipt_no}/regenerate/`
- **Description:** Queue PDF regeneration task
- **Response:** {"status": "queued"}
- **Permissions:** IsCommitteeOfficer

### Fee Collections

#### 5. **List Fee Collections** `GET /fee-collections/`
- **Querystring Filters:**
  - `fee_type=` (membership | renewal | royalty | visitor_entry | other)
  - `payment_status=` (paid | due | partial)
  - `member=` (member ID)
  - `search=` - Search by member__full_name, member__citizenship_no
- **Response Fields:**
  - `id`, `member`, `member_name` (read-only)
  - `fee_type`, `amount`, `amount_paid`
  - `payment_status` (auto-calculated: full if amount_paid >= amount, partial if > 0, else due)
  - `receipt_no` (read-only), `description`
  - `created_at`, `updated_at`
- **Permissions:** IsCommitteeOfficer | IsAuthenticatedReadOnly

#### 6. **Create Fee Collection** `POST /fee-collections/`
- **Request Body:**
  - `member` (integer, optional for non-member fees)
  - `fee_type` (choice: membership | renewal | royalty | visitor_entry | other, required)
  - `amount` (decimal, required, minimum 0.01)
  - `amount_paid` (decimal, default: 0)
  - `description` (text)
- **Auto-Calculation:**
  - If `amount_paid >= amount`: `payment_status = paid`
  - Else if `amount_paid > 0`: `payment_status = partial`
  - Else: `payment_status = due`
- **Response:** Created fee collection object

#### 7. **Get Fee Collection** `GET /fee-collections/{id}/`

#### 8. **Update Fee Collection** `PATCH /fee-collections/{id}/`
- **Editable:** amount_paid, description
- **Auto-Updates:** payment_status based on amount_paid

#### 9. **Delete Fee Collection** `DELETE /fee-collections/{id}/`

---

## GOVERNANCE MODULE
**Endpoint Base:** `/api/v1/governance/`

### Committee Members

#### 1. **List Committee Members** `GET /committee-members/`
- **Querystring Filters:**
  - `position=` (chair | vice_chair | secretary | joint_secretary | treasurer | member)
  - `status=` (active | vacant | removed)
  - `term_start=` (date filter)
  - `term_end=` (date filter)
  - `search=` - Search by member__full_name, position
- **Response Fields:**
  - `id`, `member`, `member_name` (read-only)
  - `position`, `gender`, `caste_ethnicity`
  - `term_start`, `term_end`, `status`
  - `subcommittees` (array of IDs), `subcommittee_names` (read-only array of names)
  - `created_at`, `updated_at`
- **Permissions:** IsCommitteeOfficer | IsMember | IsSubCommitteeMember | IsAuthenticatedReadOnly

#### 2. **Create Committee Member** `POST /committee-members/`
- **Request Body:**
  - `member` (integer, required)
  - `position` (choice, required)
  - `gender` (string, required)
  - `caste_ethnicity` (string)
  - `term_start` (date, required)
  - `term_end` (date, required)
  - `status` (choice: active | vacant | removed, default: active)
  - `subcommittees` (array of subcommittee IDs)
- **Response:** Created committee member

#### 3. **Quota Status** `GET /committee-members/quota_status/`
- **Description:** Check committee composition against bylaws (gender, caste quotas)
- **Response:** Quota status object

#### 4. **Get/Update/Delete Committee Member** `GET|PATCH|DELETE /committee-members/{id}/`

### Elections

#### 5. **List Elections** `GET /elections/`
- **Querystring Filters:**
  - `status=` (in_progress | completed)
  - `election_date=` (date filter)
- **Response Fields:**
  - `id`, `election_committee_members`, `election_date`
  - `status`, `candidates` (array of candidate objects, read-only)
  - `created_at`, `updated_at`
- **Permissions:** IsCommitteeOfficer | IsMember | IsSubCommitteeMember | IsAuthenticatedReadOnly

#### 6. **Create Election** `POST /elections/`
- **Request Body:**
  - `election_committee_members` (string, required - names/designations)
  - `election_date` (date, required)
  - `status` (choice: in_progress | completed, default: in_progress)
- **Response:** Created election

#### 7. **Get/Update/Delete Election** `GET|PATCH|DELETE /elections/{id}/`

### Candidates

#### 8. **List Candidates** `GET /candidates/`
- **Querystring Filters:**
  - `election=` (election ID)
  - `result=` (elected | not_elected)
- **Response Fields:**
  - `id`, `election`, `member`, `member_name` (read-only)
  - `position_applied`, `votes_received`, `result`
- **Permissions:** IsCommitteeOfficer | IsMember | IsSubCommitteeMember | IsAuthenticatedReadOnly

#### 9. **Create/Read/Update/Delete Candidate** `POST|GET|PATCH|DELETE /candidates/{id}/`
- **Request Body:**
  - `election` (integer, required)
  - `member` (integer, required)
  - `position_applied` (string, required)
  - `votes_received` (integer, default: 0)
  - `result` (choice: elected | not_elected, default: not_elected)

### SubCommittees

#### 10. **List SubCommittees** `GET /subcommittees/`
- **Querystring Filters:**
  - `name=` (predefined choices)
  - `search=` - Search by name
- **Response Fields:**
  - `id`, `name`, `tor_description` (Terms of Reference)
  - `created_at`, `updated_at`
- **SubCommittee Names:**
  - account_fund | dispute_resolution | infrastructure | monitoring | livelihood | anti_poaching | fire_control | youth_sports | women | other
- **Permissions:** IsCommitteeOfficer | IsMember | IsSubCommitteeMember | IsAuthenticatedReadOnly

#### 11. **Create/Read/Update/Delete SubCommittee** `POST|GET|PATCH|DELETE /subcommittees/{id}/`

### Oath Records

#### 12. **List Oath Records** `GET /oath-records/`
- **Querystring Filters:**
  - `oath_date=` (date filter)
- **Response Fields:**
  - `id`, `committee_member`, `committee_member_name` (read-only)
  - `oath_date`
- **Permissions:** IsCommitteeOfficer | IsMember | IsSubCommitteeMember | IsAuthenticatedReadOnly

#### 13. **Create/Read/Update/Delete Oath Record** `POST|GET|PATCH|DELETE /oath-records/{id}/`

### No-Confidence Motions

#### 14. **List No-Confidence Motions** `GET /no-confidence-motions/`
- **Querystring Filters:**
  - `target_type=` (full_committee | single_officer)
  - `assembly_decision=` (pending | passed | failed)
- **Response Fields:**
  - `id`, `target_type`
  - `target_committee_member` (required if single_officer, else null)
  - `signatures_count`, `filed_date`
  - `assembly_decision`, `created_at`, `updated_at`
- **Permissions:** IsCommitteeOfficer | IsMember | IsSubCommitteeMember | IsAuthenticatedReadOnly

#### 15. **Create/Read/Update/Delete No-Confidence Motion** `POST|GET|PATCH|DELETE /no-confidence-motions/{id}/`
- **Validation:** If target_type == single_officer, target_committee_member is required

### Handover Records

#### 16. **List Handover Records** `GET /handover-records/`
- **Querystring Filters:**
  - `status=` (pending | completed | escalated)
  - `deadline_date=` (date filter)
- **Response Fields:**
  - `id`, `outgoing_committee_member`, `outgoing_name` (read-only)
  - `incoming_committee_member`, `incoming_name` (read-only)
  - `cash_amount`, `assets_summary`
  - `deadline_date`, `completed_date`, `status`
  - `created_at`, `updated_at`
- **Permissions:** IsCommitteeOfficer

#### 17. **Create/Read/Update/Delete Handover Record** `POST|GET|PATCH|DELETE /handover-records/{id}/`
- **Request Body:**
  - `outgoing_committee_member` (integer, required)
  - `incoming_committee_member` (integer, optional)
  - `cash_amount` (decimal, default: 0, minimum 0)
  - `assets_summary` (text)
  - `deadline_date` (date, required)
  - `completed_date` (date, optional)
  - `status` (choice: pending | completed | escalated, default: pending)

---

## FUND MODULE
**Endpoint Base:** `/api/v1/fund/`

### Fund Allocation Rules

#### 1. **List Allocation Rules** `GET /allocation-rules/`
- **Response Fields:**
  - `id`, `forest_dev_min_percent`, `poor_targeted_min_percent`
  - `effective_from`, `created_at`, `updated_at`
- **Permissions:** IsCommitteeOfficer | IsAuthenticatedReadOnly

#### 2. **Create/Read/Update/Delete Allocation Rule** `POST|GET|PATCH|DELETE /allocation-rules/{id}/`

### Bank Accounts

#### 3. **List Bank Accounts** `GET /bank-accounts/`
- **Response Fields:**
  - `id`, `bank_name`, `account_number`
  - `signatories` (array of committee member IDs)
  - `min_signatures_required`, `created_at`, `updated_at`
- **Validation:** At least one signatory must be female per bylaws
- **Permissions:** IsCommitteeOfficer | IsSubCommitteeMember | IsAuthenticatedReadOnly

#### 4. **Create/Read/Update/Delete Bank Account** `POST|GET|PATCH|DELETE /bank-accounts/{id}/`
- **Request Body:**
  - `bank_name` (string, required)
  - `account_number` (string, required)
  - `signatories` (array of committee member IDs, required)
  - `min_signatures_required` (integer, default: 1)

### Cash Transactions

#### 5. **List Cash Transactions** `GET /cash-transactions/`
- **Querystring Filters:**
  - `type=` (income | expense)
  - `source_or_purpose=` (search/filter)
- **Response Fields:**
  - `id`, `type`, `source_or_purpose`, `amount`
  - `requires_committee_approval` (read-only, auto-calculated)
  - `approved_by`, `created_at`, `updated_at`
- **Permissions:** IsCommitteeOfficer | IsSubCommitteeMember | IsAuthenticatedReadOnly

#### 6. **Create Cash Transaction** `POST /cash-transactions/`
- **Request Body:**
  - `type` (choice: income | expense, required)
  - `source_or_purpose` (string, required)
  - `amount` (decimal, required, minimum 0.01)
  - `approved_by` (integer, optional but required if amount exceeds approval limits)
- **Auto-Calculation:**
  - `requires_committee_approval` = true if amount > min(cash_chair_approval_limit, cash_treasurer_approval_limit)
- **Validation:** Large transactions require approval before save
- **Permissions:** IsCommitteeOfficer | IsSubCommitteeMember

#### 7. **Get/Update/Delete Cash Transaction** `GET|PATCH|DELETE /cash-transactions/{id}/`

### Audits

#### 8. **List Audits** `GET /audits/`
- **Querystring Filters:**
  - `fiscal_year=` (e.g., "2082/83")
  - `audit_tier=` (internal | external)
- **Response Fields:**
  - `id`, `fiscal_year`, `total_income`
  - `audit_tier` (read-only, auto-determined: external if > threshold, else internal)
  - `auditor_name`, `findings`, `irregularities_recovered`
  - `created_at`, `updated_at`
- **Permissions:** IsCommitteeOfficer | IsSubCommitteeMember | IsAuthenticatedReadOnly

#### 9. **Create/Read/Update/Delete Audit** `POST|GET|PATCH|DELETE /audits/{id}/`
- **Request Body:**
  - `fiscal_year` (string, required)
  - `total_income` (decimal, required, minimum 0)
  - `auditor_name` (string, required)
  - `findings` (text)
  - `irregularities_recovered` (decimal, default: 0, minimum 0)
- **Note:** `audit_tier` auto-calculated based on total_income vs audit_external_threshold

### Public Audits

#### 10. **List Public Audits** `GET /public-audits/`
- **Querystring Filters:**
  - `fiscal_year=` (string filter)
  - `assembly_approval=` (true | false)
- **Response Fields:**
  - `id`, `fiscal_year`, `presentation_date`
  - `assembly_approval`, `created_at`, `updated_at`
- **Permissions:** IsCommitteeOfficer | IsAuthenticatedReadOnly

#### 11. **Create/Read/Update/Delete Public Audit** `POST|GET|PATCH|DELETE /public-audits/{id}/`

---

## LIVELIHOOD MODULE
**Endpoint Base:** `/api/v1/livelihood/`

### Revolving Fund Loans

#### 1. **List Loans** `GET /revolving-loans/`
- **Querystring Filters:**
  - `status=` (active | repaid | defaulted)
  - `issue_date=` (date filter)
- **Response Fields:**
  - `id`, `household`, `household_name` (read-only)
  - `amount`, `issue_date`, `repaid_amount`, `status`
  - `created_at`, `updated_at`
- **Permissions:** IsCommitteeOfficer | IsSubCommitteeMember | IsMember | IsAuthenticatedReadOnly
- **Access Control:** Members see only their household loans

#### 2. **Create Loan** `POST /revolving-loans/`
- **Request Body:**
  - `household` (integer, required)
  - `amount` (decimal, required, minimum 0.01)
  - `issue_date` (date, required)
  - `repaid_amount` (decimal, default: 0)
- **Validation:** Household must be POOR wealth class
- **Response:** Created loan with status=active

#### 3. **Get/Update/Delete Loan** `GET|PATCH|DELETE /revolving-loans/{id}/`

### Livelihood Program Records

#### 4. **List Programs** `GET /program-records/`
- **Querystring Filters:**
  - `program_type=` (skill_training | livestock | agriculture | other)
  - `program_date=` (date filter)
- **Response Fields:**
  - `id`, `household`, `household_name` (read-only)
  - `program_type`, `amount_or_value`, `program_date`, `description`
  - `created_at`, `updated_at`
- **Permissions:** IsCommitteeOfficer | IsSubCommitteeMember | IsMember | IsAuthenticatedReadOnly
- **Access Control:** Members see only their household programs

#### 5. **Create Program** `POST /program-records/`
- **Request Body:**
  - `household` (integer, required)
  - `program_type` (choice: skill_training | livestock | agriculture | other, required)
  - `amount_or_value` (decimal, required, minimum 0.01)
  - `program_date` (date, required)
  - `description` (text)
- **Validation:** Household must be POOR wealth class
- **Response:** Created program record

#### 6. **Get/Update/Delete Program** `GET|PATCH|DELETE /program-records/{id}/`

### Poverty Group Agreements

#### 7. **List Agreements** `GET /poverty-group-agreements/`
- **Querystring Filters:**
  - `status=` (active | ended | terminated_early)
  - `search=` - Search by subgroup_name
- **Response Fields:**
  - `id`, `subgroup_name`
  - `member_households` (array of household IDs)
  - `forest_land_area`, `term_start`, `term_end`
  - `revenue_share_percent`, `status`
  - `created_at`, `updated_at`
- **Permissions:** IsCommitteeOfficer | IsSubCommitteeMember | IsMember | IsAuthenticatedReadOnly
- **Access Control:** Members see only agreements they belong to

#### 8. **Create Agreement** `POST /poverty-group-agreements/`
- **Request Body:**
  - `subgroup_name` (string, required)
  - `member_households` (array of household IDs, required)
  - `forest_land_area` (decimal, required, minimum 0)
  - `term_start` (date, required)
  - `term_end` (date, required)
  - `revenue_share_percent` (decimal, required, 0-100)
  - `status` (choice: active | ended | terminated_early, default: active)
- **Response:** Created agreement

#### 9. **Get/Update/Delete Agreement** `GET|PATCH|DELETE /poverty-group-agreements/{id}/`

---

## OFFENSE MODULE
**Endpoint Base:** `/api/v1/offense/`

### Offense Reports

#### 1. **List Offense Reports** `GET /reports/`
- **Querystring Filters:**
  - `status=` (reported | investigating | resolved | escalated_to_court)
  - `offense_type=` (text search)
  - `report_date=` (date filter)
  - `search=` - Search by accused_name, offense_type
- **Response Fields:**
  - `id`, `reported_by`, `accused_name`
  - `offense_type`, `description`, `report_date`
  - `status`, `damage_value`, `fine_amount`, `resolution`
  - `informant`, `evidence_count` (read-only), `hearings_count` (read-only)
  - `created_at`, `updated_at`
- **Permissions:** IsCommitteeOfficer | IsMember | IsSubCommitteeMember | IsAuthenticatedReadOnly

#### 2. **Create Offense Report** `POST /reports/`
- **Request Body:**
  - `reported_by` (integer, optional, auto-filled if IsMember)
  - `accused_name` (string, required)
  - `offense_type` (string, required)
  - `description` (text, required)
  - `report_date` (date, required)
  - `damage_value` (decimal, optional, minimum 0)
  - `fine_amount` (decimal, optional, minimum 0)
  - `informant` (integer, optional)
- **Response:** Created report with status=reported

#### 3. **Get/Update/Delete Offense Report** `GET|PATCH|DELETE /reports/{id}/`

#### 4. **Resolve Offense** `POST /reports/{id}/resolve/`
- **Description:** Committee resolves an offense and optionally awards informant reward
- **Request Body:**
  - `resolution` (choice: fine_paid | escalated | dismissed, required)
  - `informant_id` (integer, optional)
- **Permissions:** IsCommitteeOfficer
- **Response:** Updated offense report

### Evidence Items

#### 5. **List Evidence** `GET /evidence/`
- **Querystring Filters:**
  - `offense=` (offense ID)
  - `item_type=` (tool | weapon | vehicle | forest_product)
- **Response Fields:**
  - `id`, `offense`, `item_type`, `description`
  - `confiscated_date`, `created_at`
- **Permissions:** IsCommitteeOfficer | IsSubCommitteeMember | IsAuthenticatedReadOnly

#### 6. **Create/Read/Update/Delete Evidence Item** `POST|GET|PATCH|DELETE /evidence/{id}/`
- **Request Body:**
  - `offense` (integer, required)
  - `item_type` (choice: tool | weapon | vehicle | forest_product, required)
  - `description` (text, required)
  - `confiscated_date` (date, required)

### Hearing Records

#### 7. **List Hearings** `GET /hearings/`
- **Querystring Filters:**
  - `offense=` (offense ID)
  - `hearing_date=` (date filter)
- **Response Fields:**
  - `id`, `offense`, `accused_statement`
  - `hearing_date`, `outcome`, `created_at`
- **Permissions:** IsCommitteeOfficer | IsSubCommitteeMember | IsAuthenticatedReadOnly

#### 8. **Create/Read/Update/Delete Hearing Record** `POST|GET|PATCH|DELETE /hearings/{id}/`
- **Request Body:**
  - `offense` (integer, required)
  - `accused_statement` (text)
  - `hearing_date` (date, required)
  - `outcome` (choice: admitted | denied, required)

### Informant Rewards

#### 9. **List Informant Rewards** `GET /informant-rewards/`
- **Querystring Filters:**
  - `offense=` (offense ID)
  - `informant=` (informant member ID)
- **Response Fields:**
  - `id`, `offense`, `informant`, `reward_amount`, `paid_date`, `created_at`
- **Permissions:** IsCommitteeOfficer | IsAuthenticatedReadOnly
- **Note:** Read-only viewset (no create via direct API, created through offense resolution)

### Patrol Logs

#### 10. **List Patrol Logs** `GET /patrol-logs/`
- **Querystring Filters:**
  - `watcher=` (member ID)
  - `patrol_date=` (date filter)
- **Response Fields:**
  - `id`, `watcher`, `watcher_name` (read-only)
  - `patrol_date`, `notes`, `offense` (optional)
  - `created_at`, `updated_at`
- **Permissions:** IsCommitteeOfficer | IsSubCommitteeMember | IsAuthenticatedReadOnly

#### 11. **Create/Read/Update/Delete Patrol Log** `POST|GET|PATCH|DELETE /patrol-logs/{id}/`
- **Request Body:**
  - `watcher` (integer, required - member ID)
  - `patrol_date` (date, required)
  - `notes` (text)
  - `offense` (integer, optional)

---

## REPORTS MODULE
**Endpoint Base:** `/api/v1/reports/`

### Report Endpoints
All report endpoints return JSON by default, support PDF export with `?export=pdf` query parameter.

#### 1. **Tree Count Report** `GET /tree-count/`
- **Query Parameters:**
  - `export=pdf` - Export as PDF instead of JSON
- **JSON Response:**
  ```json
  {
    "tree_counts": [
      {
        "species": "Sal",
        "block": "Block A",
        "total_count": 150,
        "harvested_count": 10,
        "remaining_count": 140
      }
    ]
  }
  ```
- **PDF Response:** Downloadable PDF file
- **Permissions:** IsCommitteeOfficer | IsAuthenticatedReadOnly

#### 2. **Harvest Report** `GET /harvest/`
- **JSON Response:** Summary of harvest requests by source_type and status
  ```json
  {
    "harvest_summary": [
      {
        "source_type": "member_requested",
        "status": "approved",
        "count": 5,
        "total_quantity": 50.00
      }
    ]
  }
  ```

#### 3. **Stock Register Report** `GET /stock-register/`
- **JSON Response:** Current inventory status by species and grade
  ```json
  {
    "stock_register": [
      {
        "species": "Sal",
        "grade": "A",
        "quantity_available": 100.50
      }
    ]
  }
  ```

#### 4. **Sales Report** `GET /sales/`
- **JSON Response:** Sales summary by buyer type
  ```json
  {
    "sales_summary": [
      {
        "buyer_type": "member",
        "count": 10,
        "total_quantity": 200.00,
        "total_amount": 50000.00
      }
    ]
  }
  ```

#### 5. **Visitor Entries Report** `GET /visitor-entries/`
- **JSON Response:** Visitor summary by visit purpose
  ```json
  {
    "visitor_entries": [
      {
        "visit_purpose": "general_visit",
        "count": 50,
        "total_amount": 5000.00
      }
    ]
  }
  ```

#### 6. **Fund Audit Report** `GET /fund-audit/`
- **JSON Response:** Cash flow and audit summary
  ```json
  {
    "total_income": 100000.00,
    "total_expense": 75000.00,
    "audits": [...]
  }
  ```

#### 7. **Governance Report** `GET /governance/`
- **JSON Response:** Committee and election statistics

#### 8. **Livelihood Report** `GET /livelihood/`
- **JSON Response:** Livelihood programs and loan statistics

#### 9. **Offense Report** `GET /offense/`
- **JSON Response:** Offense summary and resolution statistics

#### 10. **Annual DFO Report** `GET /annual-dfo/`
- **Description:** Comprehensive annual report for District Forest Office
- **JSON Response:** Aggregated data across all modules for fiscal year
- **PDF Response:** Formatted annual report document

---

## PERMISSIONS & ACCESS CONTROL

### Role-Based Permissions:

**Admin/Committee Officer (committee_officer):**
- Full CRUD on all resources
- Approve/reject harvest requests
- Resolve offenses
- Manage system configuration
- Approve cash transactions above limits

**Member (member):**
- View own household and member profile
- Submit harvest requests (member_requested only)
- View own livelihood records and loans
- Report offenses with own name
- Read-only access to governance/committee info

**Sub-committee Member (sub_committee_member):**
- Limited to assigned sub-committee scope
- Can view/manage records related to their sub-committee
- Read-only on most resources

**DFO Viewer (dfo_viewer):**
- Read-only access to all resources
- Generate reports

**Authenticated Read-Only:**
- Read access to most public resources
- No create/update/delete permissions

### Resource-Level Access Patterns:

1. **Household & Member**: 
   - Committee officers: Full access
   - Members: Own data only
   - Others: Limited read access

2. **Financial (Billing, Fund)**:
   - Committee officers: Full access
   - Sub-committee (Fund): Restricted to fund sub-committee members
   - Others: Limited read access

3. **Offense/Governance**:
   - Committee officers: Full CRUD
   - Members/Sub-committee: Can report/view, limited edit
   - Others: Read-only

---

## COMMON QUERYSTRING PARAMETERS

### Pagination (DRF default):
- `page=` (integer) - Page number
- `page_size=` (integer) - Records per page

### Filtering:
- `filterset_fields` defined per viewset - Use as `?field_name=value`
- Multiple values: `?field_name=value1&field_name=value2`

### Search:
- `search=` - Full-text search on `search_fields` defined in viewset

### Ordering:
- `ordering=` - Sort by field (prefix with `-` for descending)
- Multiple fields: `?ordering=field1,-field2`

### Export:
- `export=pdf` - Export to PDF (on report endpoints)
- `format=json|csv` - Some endpoints support multiple formats

---

## AUTHENTICATION

### Token-Based Authentication:
1. Login: `POST /api/v1/core/auth/login/` with email & password
2. Response includes `token` value
3. Include in all subsequent requests: `Authorization: Token <token>`

### Headers Required:
```
Authorization: Token abc123def456...
Content-Type: application/json
```

---

## ERROR RESPONSES

### Standard Error Format:
```json
{
  "detail": "Error message"
}
```

### Validation Errors:
```json
{
  "field_name": ["Error message for this field"],
  "another_field": ["Error 1", "Error 2"]
}
```

### Common HTTP Status Codes:
- `200 OK` - Successful GET/PATCH/PUT
- `201 Created` - Successful POST
- `204 No Content` - Successful DELETE
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Missing/invalid token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Server Error` - Server error

