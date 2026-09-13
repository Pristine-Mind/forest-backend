from django.utils import timezone

from rest_framework import viewsets, response, status
from rest_framework.decorators import action

from apps.core.models import Notification
from apps.core.permissions import (
    IsAuthenticatedReadOnly,
    IsCommitteeChair,
    IsSubCommitteeMember,
    BankTransactionPermission,
    IsMember,
    IsChair,
)
from apps.fund.models import (
    Audit,
    BankAccount,
    BankTransaction,
    BudgetAllocation,
    CashTransaction,
    FundAllocationRule,
    PublicAudit,
)
from apps.fund.serializers import (
    AuditSerializer,
    BankAccountSerializer,
    BankTransactionSerializer,
    BudgetAllocationSerializer,
    CashTransactionSerializer,
    FundAllocationRuleSerializer,
    PublicAuditSerializer,
    NotificationSerializer,
)


def _is_fund_subcommittee_user(user):
    from apps.governance.models import CommitteeMember, SubCommittee

    if not user.is_sub_committee_user():
        return False
    member = getattr(user, "member_profile", None)
    if not member:
        return False
    cm = CommitteeMember.objects.filter(member=member, status=CommitteeMember.Status.ACTIVE).first()
    if not cm:
        return False
    return cm.subcommittees.filter(name=SubCommittee.Name.ACCOUNT_FUND).exists()


class FundAllocationRuleViewSet(viewsets.ModelViewSet):
    queryset = FundAllocationRule.objects.all()
    serializer_class = FundAllocationRuleSerializer
    permission_classes = [IsCommitteeChair | IsAuthenticatedReadOnly]


class BankAccountViewSet(viewsets.ModelViewSet):
    queryset = BankAccount.objects.all()
    serializer_class = BankAccountSerializer
    permission_classes = [IsCommitteeChair | IsSubCommitteeMember | IsAuthenticatedReadOnly]


class CashTransactionViewSet(viewsets.ModelViewSet):
    queryset = CashTransaction.objects.all()
    serializer_class = CashTransactionSerializer
    permission_classes = [IsCommitteeChair | IsSubCommitteeMember | IsAuthenticatedReadOnly | IsMember]
    filterset_fields = ["type", "source_or_purpose", "approval_status"]

    def get_queryset(self):
        user = self.request.user
        if _is_fund_subcommittee_user(user) or user.is_dfo_viewer():
            return self.queryset
        return self.queryset

    def perform_create(self, serializer):
        """Set the creator when creating a cash transaction."""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsSubCommitteeMember | IsMember])
    def submit_for_approval(self, request, pk=None):
        """Submit cash transaction for chair approval (staff/secretary only)."""
        transaction = self.get_object()
        
        # Check if user is secretary or staff
        if not (request.user.is_secretary() or request.user.is_staff_user()):
            return response.Response(
                {"detail": "Only secretary or staff can submit transactions for approval."},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        if transaction.approval_status != CashTransaction.ApprovalStatus.DRAFT:
            return response.Response(
                {"detail": f"Can only submit DRAFT transactions. Current status: {transaction.approval_status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        transaction.approval_status = CashTransaction.ApprovalStatus.SUBMITTED
        transaction.submitted_for_approval_at = timezone.now()
        transaction.submitted_by = request.user
        transaction.save()

        # Create notification for chair with appropriate type based on payment method
        chair_user = None
        try:
            from apps.core.models import User
            chair_user = User.objects.filter(role=User.Role.COMMITTEE_CHAIR).first()
        except Exception:
            pass

        if chair_user:
            # Determine notification type based on payment method
            if transaction.payment_type == CashTransaction.PaymentType.CHEQUE:
                notification_type = Notification.Type.CHEQUE_NOTIFICATION
                description = f"{request.user.full_name} submitted a {transaction.type} transaction of {transaction.amount} for approval.\n\nPayment Method: {transaction.get_payment_type_display()}\nCheque Number: {transaction.cheque_number}\nBank Name: {transaction.cheque_bank_name}\nPurpose: {transaction.source_or_purpose}"
            elif transaction.payment_type == CashTransaction.PaymentType.DIGITAL_WALLET:
                notification_type = Notification.Type.DIGITAL_WALLET_NOTIFICATION
                description = f"{request.user.full_name} submitted a {transaction.type} transaction of {transaction.amount} for approval.\n\nPayment Method: {transaction.get_payment_type_display()}\nPurpose: {transaction.source_or_purpose}"
            else:
                notification_type = Notification.Type.CASH_APPROVAL
                description = f"{request.user.full_name} submitted a {transaction.type} transaction of {transaction.amount} for approval.\n\nPayment Method: {transaction.get_payment_type_display()}\nPurpose: {transaction.source_or_purpose}"
            
            Notification.objects.create(
                recipient=chair_user,
                notification_type=notification_type,
                title=f"{transaction.payment_type.upper()} Transaction Approval Required",
                description=description,
                action_required=True,
                content_type="CashTransaction",
                object_id=transaction.id,
            )

        serializer = self.get_serializer(transaction)
        return response.Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsChair])
    def approve(self, request, pk=None):
        """Approve cash transaction (chair only)."""
        transaction = self.get_object()
        
        if transaction.approval_status != CashTransaction.ApprovalStatus.SUBMITTED:
            return response.Response(
                {"detail": f"Can only approve SUBMITTED transactions. Current status: {transaction.approval_status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        transaction.approval_status = CashTransaction.ApprovalStatus.APPROVED
        transaction.approved_by = request.user
        transaction.approved_at = timezone.now()
        transaction.save()

        # Mark related notification as actioned
        try:
            notification = Notification.objects.filter(
                content_type="CashTransaction",
                object_id=transaction.id,
                recipient=request.user,
            ).first()
            if notification:
                notification.mark_as_actioned(request.user, "Transaction approved")
        except Exception:
            pass

        serializer = self.get_serializer(transaction)
        return response.Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsChair])
    def reject(self, request, pk=None):
        """Reject cash transaction (chair only)."""
        transaction = self.get_object()
        
        if transaction.approval_status != CashTransaction.ApprovalStatus.SUBMITTED:
            return response.Response(
                {"detail": f"Can only reject SUBMITTED transactions. Current status: {transaction.approval_status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        rejection_reason = request.data.get("rejection_reason", "No reason provided")
        transaction.approval_status = CashTransaction.ApprovalStatus.REJECTED
        transaction.rejection_reason = rejection_reason
        transaction.save()

        # Mark related notification as actioned
        try:
            notification = Notification.objects.filter(
                content_type="CashTransaction",
                object_id=transaction.id,
                recipient=request.user,
            ).first()
            if notification:
                notification.mark_as_actioned(request.user, f"Transaction rejected: {rejection_reason}")
        except Exception:
            pass

        serializer = self.get_serializer(transaction)
        return response.Response(serializer.data)


class AuditViewSet(viewsets.ModelViewSet):
    queryset = Audit.objects.all()
    serializer_class = AuditSerializer
    permission_classes = [IsCommitteeChair | IsSubCommitteeMember | IsAuthenticatedReadOnly]
    filterset_fields = ["fiscal_year", "audit_tier"]


class PublicAuditViewSet(viewsets.ModelViewSet):
    queryset = PublicAudit.objects.all()
    serializer_class = PublicAuditSerializer
    permission_classes = [IsCommitteeChair | IsAuthenticatedReadOnly]
    filterset_fields = ["fiscal_year", "assembly_approval"]


class BankTransactionViewSet(viewsets.ModelViewSet):
    queryset = BankTransaction.objects.all()
    serializer_class = BankTransactionSerializer
    permission_classes = [IsCommitteeChair | IsSubCommitteeMember | IsAuthenticatedReadOnly | BankTransactionPermission]
    filterset_fields = ["transaction_date"]

    def perform_create(self, serializer):
        """Automatically set created_by to the current user when creating a transaction."""
        serializer.save(created_by=self.request.user)


class BudgetAllocationViewSet(viewsets.ModelViewSet):
    queryset = BudgetAllocation.objects.all()
    serializer_class = BudgetAllocationSerializer
    permission_classes = [IsCommitteeChair | IsSubCommitteeMember | IsAuthenticatedReadOnly]
    filterset_fields = ["fiscal_year", "work_status"]

    @action(detail=True, methods=["post"], permission_classes=[IsCommitteeChair])
    def approve(self, request, pk=None):
        budget_allocation = self.get_object()
        if budget_allocation.work_status != BudgetAllocation.WorkStatus.PLANNED:
            return response.Response(
                {"detail": "Only planned budget allocations can be approved."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        budget_allocation.work_status = BudgetAllocation.WorkStatus.COMPLETED
        budget_allocation.approved_by = request.user
        budget_allocation.approved_date = timezone.now().date()
        budget_allocation.save()
        serializer = self.get_serializer(budget_allocation)
        return response.Response(serializer.data)


class NotificationViewSet(viewsets.ModelViewSet):
    """Centralized notification system for all types of notifications (mostly for chair)."""
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticatedReadOnly | IsCommitteeChair]
    filterset_fields = ["notification_type", "status"]
    ordering_fields = ["-created_at", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Users can only see their own notifications."""
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=True, methods=["post"])
    def mark_as_read(self, request, pk=None):
        """Mark a single notification as read."""
        notification = self.get_object()
        notification.mark_as_read()
        serializer = self.get_serializer(notification)
        return response.Response(serializer.data)

    @action(detail=False, methods=["post"])
    def mark_all_as_read(self, request):
        """Mark all unread notifications as read for the current user."""
        Notification.objects.filter(
            recipient=request.user,
            status=Notification.Status.UNREAD
        ).update(
            status=Notification.Status.READ,
            read_at=timezone.now()
        )
        count = Notification.objects.filter(
            recipient=request.user,
            status=Notification.Status.READ
        ).count()
        return response.Response({"detail": f"Marked all notifications as read. Total: {count}"})

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        """Get count of unread notifications."""
        unread_count = Notification.objects.filter(
            recipient=request.user,
            status=Notification.Status.UNREAD
        ).count()
        return response.Response({"unread_count": unread_count})

    @action(detail=False, methods=["get"])
    def pending_approvals(self, request):
        """Get all pending approvals (notifications requiring action)."""
        pending = Notification.objects.filter(
            recipient=request.user,
            status__in=[Notification.Status.UNREAD, Notification.Status.READ],
            action_required=True
        ).order_by("-created_at")
        serializer = self.get_serializer(pending, many=True)
        return response.Response(serializer.data)
