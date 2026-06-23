from django.db.models import Count, Sum
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import IsAuthenticatedReadOnly, IsCommitteeOfficer
from apps.forest.models import TreeCountRegister
from apps.fund.models import Audit, CashTransaction
from apps.governance.models import CommitteeMember, Election
from apps.harvest.models import HarvestRequest
from apps.inventory.models import Sale, StockLedger
from apps.livelihood.models import LivelihoodProgramRecord, RevolvingFundLoan
from apps.members.models import Household, Member
from apps.offense.models import OffenseReport
from apps.reports import pdf
from apps.visitors.models import OfficialGuestLog, VisitorEntry


class ReportsViewSet(viewsets.ViewSet):
    permission_classes = [IsCommitteeOfficer | IsAuthenticatedReadOnly]

    def _pdf_response(self, buffer, filename):
        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    def _is_pdf(self, request):
        # Use `export=pdf` rather than `format=pdf` to avoid DRF's format suffix parsing.
        return request.query_params.get("export") == "pdf"

    @action(detail=False, methods=["get"])
    def tree_count(self, request):
        data = []
        for reg in TreeCountRegister.objects.select_related("species", "block"):
            data.append(
                {
                    "species": reg.species.species_name,
                    "block": reg.block.block_name if reg.block else None,
                    "total_count": reg.total_count,
                    "harvested_count": reg.harvested_count,
                    "remaining_count": reg.remaining_count,
                }
            )
        if self._is_pdf(request):
            return self._pdf_response(pdf.generate_tree_count_pdf(data), "tree_count_report.pdf")
        return Response({"tree_counts": data})

    @action(detail=False, methods=["get"])
    def harvest(self, request):
        qs = HarvestRequest.objects.values("source_type", "status").annotate(
            count=Count("id"), total_quantity=Sum("quantity")
        )
        data = list(qs)
        if self._is_pdf(request):
            return self._pdf_response(pdf.generate_harvest_pdf(data), "harvest_report.pdf")
        return Response({"harvest_summary": data})

    @action(detail=False, methods=["get"])
    def stock_register(self, request):
        data = []
        for ledger in StockLedger.objects.select_related("species"):
            data.append(
                {
                    "species": ledger.species.species_name,
                    "grade": ledger.grade,
                    "quantity_available": ledger.quantity_available,
                }
            )
        if self._is_pdf(request):
            return self._pdf_response(pdf.generate_stock_register_pdf(data), "stock_register.pdf")
        return Response({"stock_register": data})

    @action(detail=False, methods=["get"])
    def sales(self, request):
        qs = Sale.objects.values("buyer_type").annotate(
            count=Count("id"), total_quantity=Sum("quantity"), total_amount=Sum("total_amount")
        )
        data = list(qs)
        if self._is_pdf(request):
            return self._pdf_response(pdf.generate_sales_pdf(data), "sales_report.pdf")
        return Response({"sales_summary": data})

    @action(detail=False, methods=["get"])
    def visitor_entries(self, request):
        qs = VisitorEntry.objects.values("visit_purpose").annotate(count=Count("id"), total_amount=Sum("total_amount"))
        data = list(qs)
        if self._is_pdf(request):
            return self._pdf_response(pdf.generate_visitor_entries_pdf(data), "visitor_entries_report.pdf")
        return Response({"visitor_entries": data})

    @action(detail=False, methods=["get"])
    def fund_audit(self, request):
        income = (
            CashTransaction.objects.filter(type=CashTransaction.Type.INCOME).aggregate(total=Sum("amount"))["total"] or 0
        )
        expense = (
            CashTransaction.objects.filter(type=CashTransaction.Type.EXPENSE).aggregate(total=Sum("amount"))["total"] or 0
        )
        audits = Audit.objects.values("fiscal_year", "audit_tier", "auditor_name", "total_income")
        data = {
            "total_income": income,
            "total_expense": expense,
            "net": income - expense,
            "audits": list(audits),
        }
        if self._is_pdf(request):
            return self._pdf_response(pdf.generate_fund_audit_pdf(data), "fund_audit_report.pdf")
        return Response(data)

    @action(detail=False, methods=["get"])
    def governance(self, request):
        total = CommitteeMember.objects.count()
        female = CommitteeMember.objects.filter(gender__iexact="female").count()
        elections = Election.objects.count()
        data = {
            "committee_total": total,
            "female_members": female,
            "elections_held": elections,
        }
        if self._is_pdf(request):
            return self._pdf_response(pdf.generate_governance_pdf(data), "governance_report.pdf")
        return Response(data)

    @action(detail=False, methods=["get"])
    def livelihood(self, request):
        loans = RevolvingFundLoan.objects.values("status").annotate(count=Count("id"), total=Sum("amount"))
        programs = LivelihoodProgramRecord.objects.values("program_type").annotate(
            count=Count("id"), total=Sum("amount_or_value")
        )
        data = {"loans": list(loans), "programs": list(programs)}
        if self._is_pdf(request):
            return self._pdf_response(pdf.generate_livelihood_pdf(data), "livelihood_report.pdf")
        return Response(data)

    @action(detail=False, methods=["get"])
    def offense(self, request):
        by_status = OffenseReport.objects.values("status").annotate(count=Count("id"))
        fines = OffenseReport.objects.filter(resolution=OffenseReport.Resolution.FINE_PAID).aggregate(
            total_fines=Sum("fine_amount"), total_rewards=Sum("reward__reward_amount")
        )
        data = {
            "by_status": list(by_status),
            "total_fines": fines["total_fines"] or 0,
            "total_rewards": fines["total_rewards"] or 0,
        }
        if self._is_pdf(request):
            return self._pdf_response(pdf.generate_offense_pdf(data), "offense_report.pdf")
        return Response(data)

    @action(detail=False, methods=["get"])
    def annual_dfo(self, request):
        data = {
            "members": Member.objects.count(),
            "households": Household.objects.count(),
            "tree_species": TreeCountRegister.objects.values("species__species_name").distinct().count(),
            "harvest_requests": HarvestRequest.objects.count(),
            "sales": Sale.objects.count(),
            "visitor_entries": VisitorEntry.objects.count(),
            "official_guests": OfficialGuestLog.objects.count(),
            "cash_income": CashTransaction.objects.filter(type=CashTransaction.Type.INCOME).aggregate(total=Sum("amount"))[
                "total"
            ]
            or 0,
            "cash_expense": CashTransaction.objects.filter(type=CashTransaction.Type.EXPENSE).aggregate(total=Sum("amount"))[
                "total"
            ]
            or 0,
        }
        if self._is_pdf(request):
            return self._pdf_response(pdf.generate_annual_dfo_pdf(data), "annual_dfo_report.pdf")
        return Response(data)
