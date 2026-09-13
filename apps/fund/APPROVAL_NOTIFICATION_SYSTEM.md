# Cash Transaction Approval & Centralized Notification System

## Overview

A comprehensive approval workflow system for cash transactions combined with a centralized notification platform. Staff/Secretary can submit transactions for approval, and the Committee Chair approves/rejects them. All notifications are tracked in a single system that can be extended for other notification types.

## System Architecture

### Three Main Components

1. **Cash Transaction Workflow** - Staff/Secretary submit, Chair approves/rejects
2. **Notification System** - Centralized tracking of all notification types
3. **Chair Dashboard** - View pending approvals and manage notifications

## Cash Transaction Workflow

### Transaction Lifecycle

```
DRAFT
  ↓
[Staff/Secretary submits for approval]
  ↓
SUBMITTED (notification sent to chair)
  ↓
APPROVED or REJECTED
  ↓
[Notification marked as actioned]
```

### States

| State | Created By | Can Modify | Next States | Notes |
|-------|-----------|-----------|------------|-------|
| **DRAFT** | Staff/Secretary/Chair | Creator | SUBMITTED | Initial state, not reviewed |
| **SUBMITTED** | Staff/Secretary | Chair only | APPROVED, REJECTED | Awaiting chair approval |
| **APPROVED** | Chair | - | - | Transaction approved and finalized |
| **REJECTED** | Chair | - | - | Transaction rejected with reason |

## API Endpoints

### Cash Transactions

#### Create Cash Transaction (Draft)
```http
POST /api/fund/cash-transactions/
Content-Type: application/json

{
  "type": "expense",
  "payment_type": "cash",
  "source_or_purpose": "Community meeting expenses",
  "amount": "5000.00"
}
```

**Response:** 201 Created
```json
{
  "id": 1,
  "type": "expense",
  "payment_type": "cash",
  "source_or_purpose": "Community meeting expenses",
  "amount": "5000.00",
  "requires_committee_approval": false,
  "approval_status": "draft",
  "submitted_for_approval_at": null,
  "submitted_by": null,
  "submitted_by_name": null,
  "approved_by": null,
  "approved_by_name": null,
  "approved_at": null,
  "rejection_reason": "",
  "created_at": "2026-09-12T14:30:00Z",
  "updated_at": "2026-09-12T14:30:00Z"
}
```

#### Submit Cash Transaction for Approval
Staff or Secretary can submit a draft transaction for chair approval.

```http
POST /api/fund/cash-transactions/{id}/submit_for_approval/
Content-Type: application/json
```

**Permission:** Secretary or Staff only

**Response:** 200 OK
```json
{
  "id": 1,
  "approval_status": "submitted",
  "submitted_for_approval_at": "2026-09-12T14:35:00Z",
  "submitted_by": 3,
  "submitted_by_name": "Jane Smith"
}
```

**Error Responses:**

403 Forbidden - User is not secretary or staff
```json
{
  "detail": "Only secretary or staff can submit transactions for approval."
}
```

400 Bad Request - Transaction not in DRAFT status
```json
{
  "detail": "Can only submit DRAFT transactions. Current status: approved"
}
```

#### Chair: Approve Cash Transaction
Committee Chair approves a submitted transaction.

```http
POST /api/fund/cash-transactions/{id}/approve/
Content-Type: application/json
```

**Permission:** Committee Chair only

**Response:** 200 OK
```json
{
  "id": 1,
  "approval_status": "approved",
  "approved_by": 1,
  "approved_by_name": "John Doe",
  "approved_at": "2026-09-12T15:00:00Z"
}
```

**Side Effects:**
- Updates transaction status to APPROVED
- Sets `approved_by` and `approved_at`
- Marks related notification as ACTIONED

#### Chair: Reject Cash Transaction
Committee Chair rejects a submitted transaction with a reason.

```http
POST /api/fund/cash-transactions/{id}/reject/
Content-Type: application/json

{
  "rejection_reason": "Amount exceeds budget allocation for this quarter"
}
```

**Permission:** Committee Chair only

**Response:** 200 OK
```json
{
  "id": 1,
  "approval_status": "rejected",
  "rejection_reason": "Amount exceeds budget allocation for this quarter"
}
```

**Side Effects:**
- Updates transaction status to REJECTED
- Stores rejection reason
- Marks related notification as ACTIONED

### Query Parameters for Cash Transactions

Filter transactions:
```http
GET /api/fund/cash-transactions/?approval_status=submitted
GET /api/fund/cash-transactions/?approval_status=approved
GET /api/fund/cash-transactions/?type=expense
GET /api/fund/cash-transactions/?approval_status=rejected&approval_status=submitted
```

## Notification System

### Notification Model

```python
class Notification:
    # Who receives it
    recipient: User  # Usually the chair
    
    # What type
    notification_type: str  # CASH_APPROVAL, BANK_APPROVAL, etc.
    title: str
    description: str
    
    # Status
    status: str  # UNREAD, READ, ACTIONED
    
    # Linked to action
    content_type: str  # "CashTransaction", "BankTransaction", etc.
    object_id: int  # ID of the related transaction
    
    # Requires action
    action_required: bool
    action_deadline: datetime
    
    # Action tracking
    read_at: datetime
    actioned_at: datetime
    actioned_by: User
    action_notes: str
```

### Notification Types

| Type | Triggered By | Recipient | Example |
|------|-------------|-----------|---------|
| `CASH_APPROVAL` | Submit cash transaction | Chair | "Staff submitted $5000 expense" |
| `BANK_APPROVAL` | Submit bank transaction | Chair | "Bank deposit recorded" |
| `BUDGET_APPROVAL` | Budget allocation | Chair | "Budget approval needed" |
| `HARVEST_APPROVAL` | Harvest submission | Chair | "Harvest approval needed" |
| `MEMBER_REQUEST` | Member action | Chair | "New membership request" |
| `SYSTEM_ALERT` | System event | Various | "System maintenance" |
| `OFFENSE_REPORT` | Offense recorded | Chair | "Forest offense reported" |
| `ELECTION_NOTICE` | Election event | Members | "Election scheduled" |

### Notification Endpoints

#### List Notifications
Get all notifications for current user.

```http
GET /api/v1/fund/notifications/
```

**Response:** 200 OK
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "recipient": 1,
      "recipient_name": "John Doe (Chair)",
      "notification_type": "cash_approval",
      "title": "Cash Transaction Approval Required",
      "description": "Jane Smith submitted an expense transaction of 5000 for approval.\n\nPurpose: Community meeting expenses",
      "status": "unread",
      "content_type": "CashTransaction",
      "object_id": 1,
      "action_required": true,
      "action_deadline": null,
      "read_at": null,
      "actioned_at": null,
      "actioned_by": null,
      "actioned_by_name": null,
      "action_notes": "",
      "created_at": "2026-09-12T14:35:00Z",
      "updated_at": "2026-09-12T14:35:00Z"
    }
  ]
}
```

#### Mark Single Notification as Read
```http
POST /api/v1/fund/notifications/{id}/mark_as_read/
```

**Response:** 200 OK
```json
{
  "status": "read",
  "read_at": "2026-09-12T14:40:00Z"
}
```

#### Mark All Notifications as Read
```http
POST /api/v1/fund/notifications/mark_all_as_read/
```

**Response:** 200 OK
```json
{
  "detail": "Marked all notifications as read. Total: 5"
}
```

#### Get Unread Count
```http
GET /api/v1/fund/notifications/unread_count/
```

**Response:** 200 OK
```json
{
  "unread_count": 3
}
```

#### Get Pending Approvals
Get only notifications that require action.

```http
GET /api/v1/fund/notifications/pending_approvals/
```

**Response:** 200 OK
```json
[
  {
    "id": 1,
    "notification_type": "cash_approval",
    "title": "Cash Transaction Approval Required",
    "action_required": true,
    "content_type": "CashTransaction",
    "object_id": 1,
    "created_at": "2026-09-12T14:35:00Z"
  }
]
```

### Filter Notifications

By type:
```http
GET /api/v1/fund/notifications/?notification_type=cash_approval
```

By status:
```http
GET /api/v1/fund/notifications/?status=unread
GET /api/v1/fund/notifications/?status=read
GET /api/v1/fund/notifications/?status=actioned
```

Multiple filters:
```http
GET /api/v1/fund/notifications/?notification_type=cash_approval&status=unread
```

## Complete User Flow Example

### Scenario: Staff submits expense for approval

#### Step 1: Staff Creates Transaction (Draft)
```bash
curl -X POST http://localhost:8000/api/fund/cash-transactions/ \
  -H "Authorization: Bearer staff_token" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "expense",
    "payment_type": "cash",
    "source_or_purpose": "Team training materials",
    "amount": "3500.00"
  }'
```

Response:
```json
{
  "id": 42,
  "approval_status": "draft",
  "amount": "3500.00",
  "source_or_purpose": "Team training materials"
}
```

#### Step 2: Staff Submits for Approval
```bash
curl -X POST http://localhost:8000/api/fund/cash-transactions/42/submit_for_approval/ \
  -H "Authorization: Bearer staff_token" \
  -H "Content-Type: application/json"
```

Response:
```json
{
  "id": 42,
  "approval_status": "submitted",
  "submitted_by": 5,
  "submitted_by_name": "Jane Smith",
  "submitted_for_approval_at": "2026-09-12T15:30:00Z"
}
```

**Behind the scenes:** A notification is created for the chair

#### Step 3: Chair Receives Notification
Chair checks notifications:
```bash
curl -X GET http://localhost:8000/api/v1/fund/notifications/?status=unread \
  -H "Authorization: Bearer chair_token"
```

Response:
```json
{
  "results": [
    {
      "id": 1,
      "notification_type": "cash_approval",
      "title": "Cash Transaction Approval Required",
      "description": "Jane Smith submitted an expense transaction of 3500 for approval.\n\nPurpose: Team training materials",
      "status": "unread",
      "content_type": "CashTransaction",
      "object_id": 42,
      "action_required": true
    }
  ]
}
```

#### Step 4: Chair Reviews and Approves
```bash
curl -X POST http://localhost:8000/api/fund/cash-transactions/42/approve/ \
  -H "Authorization: Bearer chair_token" \
  -H "Content-Type: application/json"
```

Response:
```json
{
  "id": 42,
  "approval_status": "approved",
  "approved_by": 1,
  "approved_by_name": "John Doe",
  "approved_at": "2026-09-12T16:00:00Z"
}
```

**Behind the scenes:** The notification is marked as ACTIONED

#### Step 5: Chair Can See Actioned Notifications
```bash
curl -X GET http://localhost:8000/api/v1/fund/notifications/?status=actioned \
  -H "Authorization: Bearer chair_token"
```

Response shows the notification with status=actioned

---

### Alternative: Chair Rejects Transaction

After Step 3, instead of approving:

```bash
curl -X POST http://localhost:8000/api/fund/cash-transactions/42/reject/ \
  -H "Authorization: Bearer chair_token" \
  -H "Content-Type: application/json" \
  -d '{
    "rejection_reason": "Training budget already allocated for this quarter"
  }'
```

Response:
```json
{
  "id": 42,
  "approval_status": "rejected",
  "rejection_reason": "Training budget already allocated for this quarter"
}
```

**Staff Impact:** Staff can query the transaction and see rejection_reason to understand why it was rejected.

## Permission Matrix

### Cash Transactions

| Action | Draft | Update | Delete | Submit for Approval | Approve | Reject |
|--------|-------|--------|--------|------------------|---------|--------|
| **Chair** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Secretary** | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| **Staff** | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| **Member** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Others** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

### Notifications

| Action | List Own | Mark Read | Mark Actioned | View Details |
|--------|----------|-----------|---------------|--------------|
| **Chair** | ✅ | ✅ | ✅ | ✅ |
| **Secretary** | ✅ | ✅ | ❌ | ✅ |
| **Staff** | ✅ | ✅ | ❌ | ✅ |
| **Others** | ✅ | ✅ | ❌ | ✅ |

## Database Models

### CashTransaction
```python
- type: INCOME/EXPENSE
- payment_type: CASH/CHEQUE/DIGITAL_WALLET
- source_or_purpose: str
- amount: Decimal
- approval_status: DRAFT/SUBMITTED/APPROVED/REJECTED
- submitted_for_approval_at: datetime
- submitted_by: User (ForeignKey)
- approved_by: User (ForeignKey)
- approved_at: datetime
- rejection_reason: str
```

### Notification
```python
- recipient: User (ForeignKey)
- notification_type: Type (enum)
- title: str
- description: str
- status: UNREAD/READ/ACTIONED
- content_type: str (model name)
- object_id: int
- action_required: bool
- action_deadline: datetime
- read_at: datetime
- actioned_at: datetime
- actioned_by: User (ForeignKey)
- action_notes: str
```

## Features

### For Staff/Secretary
- ✅ Create cash transactions
- ✅ Save as draft
- ✅ Submit for chair approval
- ✅ View transaction status
- ✅ See rejection reasons
- ✅ View their own notifications
- ✅ Mark notifications as read

### For Committee Chair
- ✅ View all pending approvals
- ✅ Approve transactions
- ✅ Reject with detailed reasons
- ✅ Create transactions
- ✅ View all notifications
- ✅ Mark notifications as read/actioned
- ✅ View pending approvals summary
- ✅ Access notification dashboard

### Extensible Notification Types
The system is designed to extend to:
- Bank transaction approvals
- Budget allocation approvals
- Harvest approvals
- Member requests
- Offense reports
- Election notices
- System alerts

## Migration Notes

Run Django migrations to create the new tables:

```bash
python manage.py makemigrations
python manage.py migrate
```

This creates:
- `Notification` table in `core_notification`
- Updated `CashTransaction` table with approval workflow fields

## Testing

### Test Case: Complete Workflow
1. Create cash transaction (staff)
2. Submit for approval (staff)
3. Verify notification created (check DB)
4. Approve transaction (chair)
5. Verify notification marked as actioned (chair)

### Test Case: Rejection
1. Create cash transaction (staff)
2. Submit for approval (staff)
3. Reject with reason (chair)
4. Verify status and reason stored
5. Verify notification marked as actioned

### Test Case: Permissions
1. Try to approve as secretary → Should fail
2. Try to submit as chair → Should succeed
3. Try to reject as staff → Should fail

## Future Enhancements

1. **Email Notifications** - Send email when notification created
2. **SMS Alerts** - Send SMS for urgent approvals
3. **Automatic Escalation** - Escalate if not approved in X days
4. **Approval History** - Track all approval state changes
5. **Bulk Actions** - Approve/reject multiple at once
6. **Custom Rules** - Set auto-approval for small amounts
7. **Audit Trail** - Detailed log of all actions
8. **Reminders** - Send reminders to chair for pending approvals

## Troubleshooting

### Notification not created after submit
- Check that chair user exists and has COMMITTEE_CHAIR role
- Check Django logs for exceptions in notification creation
- Verify Notification model is migrated

### Can't submit for approval
- Verify you have SECRETARY or STAFF role
- Verify transaction is in DRAFT status
- Check permissions middleware

### Chair can't approve
- Verify you have COMMITTEE_CHAIR role
- Verify transaction is in SUBMITTED status
- Check notification permissions
