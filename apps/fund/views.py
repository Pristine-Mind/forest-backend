from django.utils import timezone

from rest_framework import viewsets, response, status
from rest_framework.decorators import action

from apps.core.permissions import (
    IsAuthenticatedReadOnly,
    IsCommitteeOfficer,
    IsSubCommitteeMember,
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
    permission_classes = [IsCommitteeOfficer | IsAuthenticatedReadOnly]


class BankAccountViewSet(viewsets.ModelViewSet):
    queryset = BankAccount.objects.all()
    serializer_class = BankAccountSerializer
    permission_classes = [IsCommitteeOfficer | IsSubCommitteeMember | IsAuthenticatedReadOnly]


class CashTransactionViewSet(viewsets.ModelViewSet):
    queryset = CashTransaction.objects.all()
    serializer_class = CashTransactionSerializer
    permission_classes = [IsCommitteeOfficer | IsSubCommitteeMember | IsAuthenticatedReadOnly]
    filterset_fields = ["type", "source_or_purpose"]

    def get_queryset(self):
        user = self.request.user
        if _is_fund_subcommittee_user(user) or user.is_dfo_viewer():
            return self.queryset
        return self.queryset


class AuditViewSet(viewsets.ModelViewSet):
    queryset = Audit.objects.all()
    serializer_class = AuditSerializer
    permission_classes = [IsCommitteeOfficer | IsSubCommitteeMember | IsAuthenticatedReadOnly]
    filterset_fields = ["fiscal_year", "audit_tier"]


class PublicAuditViewSet(viewsets.ModelViewSet):
    queryset = PublicAudit.objects.all()
    serializer_class = PublicAuditSerializer
    permission_classes = [IsCommitteeOfficer | IsAuthenticatedReadOnly]
    filterset_fields = ["fiscal_year", "assembly_approval"]


class BankTransactionViewSet(viewsets.ModelViewSet):
    queryset = BankTransaction.objects.all()
    serializer_class = BankTransactionSerializer
    permission_classes = [IsCommitteeOfficer | IsSubCommitteeMember | IsAuthenticatedReadOnly]
    filterset_fields = ["transaction_date"]


class BudgetAllocationViewSet(viewsets.ModelViewSet):
    queryset = BudgetAllocation.objects.all()
    serializer_class = BudgetAllocationSerializer
    permission_classes = [IsCommitteeOfficer | IsSubCommitteeMember | IsAuthenticatedReadOnly]
    filterset_fields = ["fiscal_year", "work_status"]

    @action(detail=True, methods=["post"], permission_classes=[IsCommitteeOfficer])
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
