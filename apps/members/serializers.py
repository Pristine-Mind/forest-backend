from decimal import Decimal

from django.db.models import Count, Q, Sum
from rest_framework import serializers

from apps.members.models import Household, Member, MembershipRenewal


class HouseholdSerializer(serializers.ModelSerializer):
    entry_fee_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    photo = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Household
        fields = [
            "id",
            "household_head_name",
            "tole",
            "wealth_class",
            "population_male",
            "population_female",
            "livestock_cattle",
            "livestock_buffalo",
            "livestock_goat",
            "education_level",
            "occupation",
            "caste_ethnicity",
            "registration_date",
            "entry_fee_type",
            "entry_fee_due",
            "status",
            "citizenship_no",
            "membership_type",
            "membership_status",
            "date_joined",
            "photo",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "entry_fee_due", "created_at", "updated_at"]


class MemberSerializer(serializers.ModelSerializer):
    household_name = serializers.CharField(source="household.household_head_name", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    member_photo = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Member
        fields = [
            "id",
            "household",
            "household_name",
            # "user",
            "user_email",
            "member_photo",
            "full_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "household_name", "user_email", "created_at", "updated_at"]


class MemberListSerializer(MemberSerializer):
    """Light serializer for list views."""

    class Meta(MemberSerializer.Meta):
        fields = [
            "id",
            "full_name",
            "household_name",
            "member_photo",
        ]
        read_only_fields = ["id", "household_name", "member_photo"]


class MembershipRenewalSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.full_name", read_only=True)

    class Meta:
        model = MembershipRenewal
        fields = [
            "id",
            "member",
            "member_name",
            "fiscal_year",
            "fee_tier",
            "fee_charged",
            "paid_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["fee_tier", "fee_charged"]


class MemberBriefSerializer(serializers.ModelSerializer):
    """Brief member information for inclusion in household stats."""

    user_email = serializers.EmailField(source="user.email", read_only=True, allow_null=True)

    class Meta:
        model = Member
        fields = ["id", "full_name", "user_email", "created_at"]


class HouseholdDetailStatsSerializer(serializers.ModelSerializer):
    """Household with comprehensive aggregated member statistics."""

    entry_fee_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    members = MemberBriefSerializer(many=True, read_only=True)

    # Member aggregation stats
    total_members = serializers.SerializerMethodField()
    member_list = serializers.SerializerMethodField()

    # Renewal stats (aggregated from all members)
    total_renewals = serializers.SerializerMethodField()
    total_renewal_fees_paid = serializers.SerializerMethodField()
    avg_fee_per_renewal = serializers.SerializerMethodField()
    members_with_renewals = serializers.SerializerMethodField()

    # Governance stats (aggregated from all members)
    total_committee_roles = serializers.SerializerMethodField()
    total_candidacies = serializers.SerializerMethodField()

    # Billing stats (aggregated from all members)
    total_fee_collections = serializers.SerializerMethodField()
    total_fees_collected = serializers.SerializerMethodField()

    # Harvest stats (aggregated from all members)
    total_harvest_requests = serializers.SerializerMethodField()
    total_approved_requests = serializers.SerializerMethodField()
    total_pending_requests = serializers.SerializerMethodField()

    # Sales stats (aggregated from all members)
    total_sales = serializers.SerializerMethodField()
    total_sales_amount = serializers.SerializerMethodField()

    # Offense stats (aggregated from all members)
    total_offense_reports_filed = serializers.SerializerMethodField()
    total_informant_rewards_received = serializers.SerializerMethodField()
    total_patrol_logs = serializers.SerializerMethodField()

    # Livelihood stats (for this household)
    total_revolving_loans = serializers.SerializerMethodField()
    total_loan_amount = serializers.SerializerMethodField()
    total_livelihood_programs = serializers.SerializerMethodField()

    class Meta:
        model = Household
        fields = [
            "id",
            "household_head_name",
            "tole",
            "citizenship_no",
            "wealth_class",
            "membership_type",
            "membership_status",
            "date_joined",
            "status",
            "population_male",
            "population_female",
            "livestock_cattle",
            "livestock_buffalo",
            "livestock_goat",
            "education_level",
            "occupation",
            "caste_ethnicity",
            "registration_date",
            "entry_fee_type",
            "entry_fee_due",
            "photo",
            "members",
            "total_members",
            "member_list",
            "total_renewals",
            "total_renewal_fees_paid",
            "avg_fee_per_renewal",
            "members_with_renewals",
            "total_committee_roles",
            "total_candidacies",
            "total_fee_collections",
            "total_fees_collected",
            "total_harvest_requests",
            "total_approved_requests",
            "total_pending_requests",
            "total_sales",
            "total_sales_amount",
            "total_offense_reports_filed",
            "total_informant_rewards_received",
            "total_patrol_logs",
            "total_revolving_loans",
            "total_loan_amount",
            "total_livelihood_programs",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_total_members(self, obj):
        return obj.members.count()

    def get_member_list(self, obj):
        return list(obj.members.values_list("full_name", flat=True))

    def get_total_renewals(self, obj):
        from apps.members.models import MembershipRenewal

        return MembershipRenewal.objects.filter(member__household=obj).count()

    def get_total_renewal_fees_paid(self, obj):
        from apps.members.models import MembershipRenewal

        total = (
            MembershipRenewal.objects.filter(member__household=obj).aggregate(Sum("fee_charged"))["fee_charged__sum"] or 0
        )
        return float(total)

    def get_avg_fee_per_renewal(self, obj):
        from apps.members.models import MembershipRenewal

        renewals = MembershipRenewal.objects.filter(member__household=obj)
        count = renewals.count()
        if count == 0:
            return 0.0
        total = renewals.aggregate(Sum("fee_charged"))["fee_charged__sum"] or 0
        return float(total / count)

    def get_members_with_renewals(self, obj):
        from apps.members.models import MembershipRenewal

        return MembershipRenewal.objects.filter(member__household=obj).values_list("member", flat=True).distinct().count()

    def get_total_committee_roles(self, obj):
        from apps.governance.models import CommitteeMember

        return CommitteeMember.objects.filter(member__household=obj).count()

    def get_total_candidacies(self, obj):
        from apps.governance.models import Candidate

        return Candidate.objects.filter(member__household=obj).count()

    def get_total_fee_collections(self, obj):
        from apps.billing.models import FeeCollection

        return FeeCollection.objects.filter(member__household=obj).count()

    def get_total_fees_collected(self, obj):
        from apps.billing.models import FeeCollection

        total = FeeCollection.objects.filter(member__household=obj).aggregate(Sum("amount_paid"))["amount_paid__sum"] or 0
        return float(total)

    def get_total_harvest_requests(self, obj):
        from apps.harvest.models import HarvestRequest

        return HarvestRequest.objects.filter(member__household=obj).count()

    def get_total_approved_requests(self, obj):
        from apps.harvest.models import HarvestRequest

        return HarvestRequest.objects.filter(member__household=obj, status="approved").count()

    def get_total_pending_requests(self, obj):
        from apps.harvest.models import HarvestRequest

        return HarvestRequest.objects.filter(member__household=obj, status="pending").count()

    def get_total_sales(self, obj):
        from apps.inventory.models import Sale

        return Sale.objects.filter(member__household=obj).count()

    def get_total_sales_amount(self, obj):
        from apps.inventory.models import Sale

        total = Sale.objects.filter(member__household=obj).aggregate(Sum("total_amount"))["total_amount__sum"] or 0
        return float(total)

    def get_total_offense_reports_filed(self, obj):
        from apps.offense.models import OffenseReport

        return OffenseReport.objects.filter(reported_by__household=obj).count()

    def get_total_informant_rewards_received(self, obj):
        from apps.offense.models import InformantReward

        total = (
            InformantReward.objects.filter(informant__household=obj).aggregate(Sum("reward_amount"))["reward_amount__sum"]
            or 0
        )
        return float(total)

    def get_total_patrol_logs(self, obj):
        from apps.offense.models import PatrolLog

        return PatrolLog.objects.filter(watcher__household=obj).count()

    def get_total_revolving_loans(self, obj):
        from apps.livelihood.models import RevolvingFundLoan

        return RevolvingFundLoan.objects.filter(household=obj).count()

    def get_total_loan_amount(self, obj):
        from apps.livelihood.models import RevolvingFundLoan

        total = RevolvingFundLoan.objects.filter(household=obj).aggregate(Sum("amount"))["amount__sum"] or 0
        return float(total)

    def get_total_livelihood_programs(self, obj):
        from apps.livelihood.models import LivelihoodProgramRecord

        return LivelihoodProgramRecord.objects.filter(household=obj).count()


class HouseholdStatsAggregateSerializer(serializers.Serializer):
    """Aggregate statistics across all households."""

    total_households = serializers.IntegerField()
    active_households = serializers.IntegerField()
    inactive_households = serializers.IntegerField()

    # Membership types
    general_households = serializers.IntegerField()
    lifetime_households = serializers.IntegerField()
    institutional_households = serializers.IntegerField()
    special_households = serializers.IntegerField()

    # Membership status
    active_memberships = serializers.IntegerField()
    inactive_memberships = serializers.IntegerField()
    cancelled_memberships = serializers.IntegerField()

    # Wealth distribution
    rich_households = serializers.IntegerField()
    medium_households = serializers.IntegerField()
    poor_households = serializers.IntegerField()

    # Member counts
    total_members = serializers.IntegerField()
    avg_members_per_household = serializers.FloatField()

    # Renewals
    total_renewals = serializers.IntegerField()
    total_renewal_fees = serializers.DecimalField(max_digits=15, decimal_places=2)

    # Governance
    total_committee_roles = serializers.IntegerField()
    total_candidacies = serializers.IntegerField()

    # Fees & Collections
    total_fee_collections = serializers.IntegerField()
    total_collected_amount = serializers.DecimalField(max_digits=15, decimal_places=2)

    # Harvest
    total_harvest_requests = serializers.IntegerField()
    approved_requests = serializers.IntegerField()
    pending_requests = serializers.IntegerField()

    # Sales
    total_sales = serializers.IntegerField()
    total_sales_amount = serializers.DecimalField(max_digits=15, decimal_places=2)

    # Offense & Patrols
    total_offense_reports = serializers.IntegerField()
    total_informant_rewards = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_patrol_logs = serializers.IntegerField()

    # Livelihood
    total_revolving_loans = serializers.IntegerField()
    total_loan_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_livelihood_programs = serializers.IntegerField()


class MemberDetailStatsSerializer(serializers.ModelSerializer):
    """Comprehensive member statistics with all system associations."""

    household_details = HouseholdSerializer(source="household", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True, allow_null=True)
    user_role = serializers.CharField(source="user.role", read_only=True, allow_null=True)

    # Renewal stats
    renewals_count = serializers.SerializerMethodField()
    total_renewal_fees_paid = serializers.SerializerMethodField()
    last_renewal = serializers.SerializerMethodField()
    current_fee_tier = serializers.SerializerMethodField()

    # Governance stats
    committee_roles_count = serializers.SerializerMethodField()
    candidacies_count = serializers.SerializerMethodField()

    # Billing stats
    fee_collections_count = serializers.SerializerMethodField()
    total_fees_collected = serializers.SerializerMethodField()

    # Harvest stats
    harvest_requests_count = serializers.SerializerMethodField()
    harvest_requests_approved = serializers.SerializerMethodField()
    harvest_requests_pending = serializers.SerializerMethodField()

    # Sale stats
    sales_count = serializers.SerializerMethodField()
    total_sales_amount = serializers.SerializerMethodField()

    # Offense stats
    offense_reports_filed = serializers.SerializerMethodField()
    informant_rewards_received = serializers.SerializerMethodField()
    patrol_logs_count = serializers.SerializerMethodField()

    # Livelihood stats (household-based)
    revolving_loans_count = serializers.SerializerMethodField()
    revolving_loans_amount = serializers.SerializerMethodField()
    livelihood_programs_count = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = [
            "id",
            "full_name",
            "household_details",
            "user_email",
            "user_role",
            "renewals_count",
            "total_renewal_fees_paid",
            "last_renewal",
            "current_fee_tier",
            "committee_roles_count",
            "candidacies_count",
            "fee_collections_count",
            "total_fees_collected",
            "harvest_requests_count",
            "harvest_requests_approved",
            "harvest_requests_pending",
            "sales_count",
            "total_sales_amount",
            "offense_reports_filed",
            "informant_rewards_received",
            "patrol_logs_count",
            "revolving_loans_count",
            "revolving_loans_amount",
            "livelihood_programs_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_renewals_count(self, obj):
        return obj.renewals.count()

    def get_total_renewal_fees_paid(self, obj):
        total = obj.renewals.aggregate(Sum("fee_charged"))["fee_charged__sum"]
        return float(total) if total else 0.0

    def get_last_renewal(self, obj):
        renewal = obj.last_renewal()
        if renewal:
            return {
                "fiscal_year": renewal.fiscal_year,
                "fee_tier": renewal.fee_tier,
                "fee_charged": float(renewal.fee_charged),
                "paid_date": renewal.paid_date,
            }
        return None

    def get_current_fee_tier(self, obj):
        from apps.core.models import SystemConfig

        config = SystemConfig.get()
        current_year = config.current_fiscal_year
        tier = obj.fee_tier_for_year(current_year)
        return tier

    def get_committee_roles_count(self, obj):
        from apps.governance.models import CommitteeMember

        return CommitteeMember.objects.filter(member=obj).count()

    def get_candidacies_count(self, obj):
        from apps.governance.models import Candidate

        return Candidate.objects.filter(member=obj).count()

    def get_fee_collections_count(self, obj):
        from apps.billing.models import FeeCollection

        return FeeCollection.objects.filter(member=obj).count()

    def get_total_fees_collected(self, obj):
        from apps.billing.models import FeeCollection

        total = FeeCollection.objects.filter(member=obj).aggregate(Sum("amount_paid"))["amount_paid__sum"]
        return float(total) if total else 0.0

    def get_harvest_requests_count(self, obj):
        from apps.harvest.models import HarvestRequest

        return HarvestRequest.objects.filter(member=obj).count()

    def get_harvest_requests_approved(self, obj):
        from apps.harvest.models import HarvestRequest

        return HarvestRequest.objects.filter(member=obj, status="approved").count()

    def get_harvest_requests_pending(self, obj):
        from apps.harvest.models import HarvestRequest

        return HarvestRequest.objects.filter(member=obj, status="pending").count()

    def get_sales_count(self, obj):
        from apps.inventory.models import Sale

        return Sale.objects.filter(member=obj).count()

    def get_total_sales_amount(self, obj):
        from apps.inventory.models import Sale

        total = Sale.objects.filter(member=obj).aggregate(Sum("total_amount"))["total_amount__sum"]
        return float(total) if total else 0.0

    def get_offense_reports_filed(self, obj):
        from apps.offense.models import OffenseReport

        return OffenseReport.objects.filter(reported_by=obj).count()

    def get_informant_rewards_received(self, obj):
        from apps.offense.models import InformantReward

        total = InformantReward.objects.filter(informant=obj).aggregate(Sum("reward_amount"))["reward_amount__sum"]
        return float(total) if total else 0.0

    def get_patrol_logs_count(self, obj):
        from apps.offense.models import PatrolLog

        return PatrolLog.objects.filter(watcher=obj).count()

    def get_revolving_loans_count(self, obj):
        from apps.livelihood.models import RevolvingFundLoan

        return RevolvingFundLoan.objects.filter(household=obj.household).count()

    def get_revolving_loans_amount(self, obj):
        from apps.livelihood.models import RevolvingFundLoan

        total = RevolvingFundLoan.objects.filter(household=obj.household).aggregate(Sum("amount"))["amount__sum"]
        return float(total) if total else 0.0

    def get_livelihood_programs_count(self, obj):
        from apps.livelihood.models import LivelihoodProgramRecord

        return LivelihoodProgramRecord.objects.filter(household=obj.household).count()


class MemberStatsAggregateSerializer(serializers.Serializer):
    """Aggregate statistics across all members or filtered members."""

    total_members = serializers.IntegerField()
    active_members = serializers.IntegerField()
    inactive_members = serializers.IntegerField()
    cancelled_members = serializers.IntegerField()

    # Membership types
    general_members = serializers.IntegerField()
    lifetime_members = serializers.IntegerField()
    institutional_members = serializers.IntegerField()
    special_members = serializers.IntegerField()

    # Wealth distribution
    rich_households = serializers.IntegerField()
    medium_households = serializers.IntegerField()
    poor_households = serializers.IntegerField()

    # Renewals
    total_renewals = serializers.IntegerField()
    total_renewal_fees = serializers.DecimalField(max_digits=15, decimal_places=2)

    # Governance
    total_committee_roles = serializers.IntegerField()
    total_candidacies = serializers.IntegerField()

    # Fees & Collections
    total_fee_collections = serializers.IntegerField()
    total_collected_amount = serializers.DecimalField(max_digits=15, decimal_places=2)

    # Harvest
    total_harvest_requests = serializers.IntegerField()
    approved_requests = serializers.IntegerField()
    pending_requests = serializers.IntegerField()

    # Sales
    total_sales = serializers.IntegerField()
    total_sales_amount = serializers.DecimalField(max_digits=15, decimal_places=2)

    # Offense & Patrols
    total_offense_reports = serializers.IntegerField()
    total_informant_rewards = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_patrol_logs = serializers.IntegerField()

    # Livelihood
    total_revolving_loans = serializers.IntegerField()
    total_loan_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_livelihood_programs = serializers.IntegerField()


class UserMemberStatsSerializer(serializers.Serializer):
    """Statistics for users with member role."""

    total_member_users = serializers.IntegerField()
    active_member_users = serializers.IntegerField()
    inactive_member_users = serializers.IntegerField()
    member_users_with_profile = serializers.IntegerField()
    member_users_without_profile = serializers.IntegerField()
    member_users_in_households = serializers.IntegerField()
    member_users_on_committees = serializers.IntegerField()
