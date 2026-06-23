from rest_framework import viewsets

from apps.core.permissions import (
    IsAuthenticatedReadOnly,
    IsCommitteeOfficer,
    IsSubCommitteeMember,
)
from apps.fund.models import (
    Audit,
    BankAccount,
    CashTransaction,
    FundAllocationRule,
    PublicAudit,
)
from apps.fund.serializers import (
    AuditSerializer,
    BankAccountSerializer,
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
