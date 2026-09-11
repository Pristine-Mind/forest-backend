from decimal import Decimal
from datetime import datetime
from typing import Optional

from django.db.models import Q, Sum, Case, When, F, DecimalField, Value
from django.utils.dateparse import parse_datetime, parse_date
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.core.models import SystemConfig
from apps.core.permissions import IsAuthenticatedReadOnly, IsCommitteeChair
from apps.inventory.models import PriceRate, Sale, StockLedger, StockTransaction, TimberLogEntry
from apps.inventory.serializers import (
    FiscalYearStockAnalysisSerializer,
    FiscalYearStockSummarySerializer,
    PriceRateSerializer,
    SaleSerializer,
    StockLedgerSerializer,
    StockTransactionSerializer,
    TimberLogEntrySerializer,
)


class StockLedgerViewSet(viewsets.ModelViewSet):
    queryset = StockLedger.objects.select_related("species")
    serializer_class = StockLedgerSerializer
    permission_classes = [IsCommitteeChair | IsAuthenticatedReadOnly]
    filterset_fields = ["species", "grade"]
    search_fields = ["species__species_name", "grade"]

    @staticmethod
    def _parse_fiscal_year(fiscal_year_str: str) -> tuple[int, int]:
        """
        Parse fiscal year string (e.g., '2082/83') to (start_year, end_year).
        Returns tuple of (start_year, end_year) as integers.
        """
        parts = fiscal_year_str.strip().split("/")
        if len(parts) != 2:
            raise ValidationError({"fiscal_year": "Invalid fiscal year format. Use format: YYYY/YY"})
        try:
            start_year = int(parts[0])
            end_year_short = int(parts[1])
            # Convert short year to full year (e.g., 83 -> 2083)
            end_year = int(str(start_year)[:2] + str(end_year_short).zfill(2))
            return start_year, end_year
        except (ValueError, IndexError):
            raise ValidationError({"fiscal_year": "Invalid fiscal year format. Use format: YYYY/YY"})

    def _get_fiscal_year_dates(self, fiscal_year_str: str) -> tuple[datetime, datetime]:
        """
        Get start and end dates for a fiscal year.
        Assumes fiscal year runs from July 15 to July 14 (Nepali fiscal year).
        """
        start_year, end_year = self._parse_fiscal_year(fiscal_year_str)
        fy_start = datetime(start_year, 7, 15)
        fy_end = datetime(end_year, 7, 14, 23, 59, 59)
        return fy_start, fy_end

    def _parse_created_before_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse created_before query parameter into datetime.
        Accepts formats: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS.
        """
        if not date_str:
            return None

        # Try parsing as datetime first (YYYY-MM-DD HH:MM:SS)
        dt = parse_datetime(date_str)
        if dt:
            return dt

        # Try parsing as date (YYYY-MM-DD) and convert to datetime at end of day
        date_obj = parse_date(date_str)
        if date_obj:
            return datetime.combine(date_obj, datetime.max.time())

        raise ValidationError({"created_before": "Invalid date format. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"})

    def _calculate_stock_for_period(
        self, stock: StockLedger, start_date: datetime, end_date: datetime, created_before: Optional[datetime] = None
    ) -> dict:
        """Calculate stock in/out for a specific period.

        Args:
            stock: StockLedger instance
            start_date: Start of fiscal period
            end_date: End of fiscal period
            created_before: Optional date filter - only include transactions created before this date
        """
        transactions = stock.transactions.filter(created_at__range=[start_date, end_date])

        # Apply created_before filter if provided
        if created_before:
            transactions = transactions.filter(created_at__lt=created_before)

        stock_in = transactions.filter(transaction_type=StockTransaction.Type.IN).aggregate(
            total=Sum("quantity", output_field=DecimalField())
        )["total"] or Decimal("0.00")

        stock_out = transactions.filter(transaction_type=StockTransaction.Type.OUT).aggregate(
            total=Sum("quantity", output_field=DecimalField())
        )["total"] or Decimal("0.00")

        return {
            "stock_in": stock_in,
            "stock_out": stock_out,
        }

    def _calculate_stock_before_period(
        self, stock: StockLedger, start_date: datetime, created_before: Optional[datetime] = None
    ) -> Decimal:
        """Calculate total stock before a specific date (opening stock).

        Args:
            stock: StockLedger instance
            start_date: Start of fiscal period (upper bound for opening stock)
            created_before: Optional date filter - only include transactions created before this date
        """
        transactions_before = stock.transactions.filter(created_at__lt=start_date)

        # Apply created_before filter if provided
        if created_before:
            transactions_before = transactions_before.filter(created_at__lt=created_before)

        total = transactions_before.aggregate(
            total=Sum(
                Case(
                    When(transaction_type=StockTransaction.Type.IN, then=F("quantity")),
                    When(transaction_type=StockTransaction.Type.OUT, then=-F("quantity")),
                    default=Value(0),
                    output_field=DecimalField(),
                )
            )
        )["total"]
        return total or Decimal("0.00")

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticatedReadOnly])
    def fiscal_year_analysis(self, request):
        """
        Get detailed stock analysis for a specific fiscal year.

        Query Parameters:
        - fiscal_year: Fiscal year in format YYYY/YY (e.g., 2082/83). Defaults to current fiscal year.
        - species: Filter by species ID (optional)
        - grade: Filter by grade (optional)
        - created_before: Only include transactions created before this date (YYYY-MM-DD or ISO format, optional)
        """
        fiscal_year = request.query_params.get("fiscal_year", SystemConfig.get().current_fiscal_year)
        created_before_str = request.query_params.get("created_before")

        try:
            fy_start, fy_end = self._get_fiscal_year_dates(fiscal_year)
            created_before = self._parse_created_before_date(created_before_str) if created_before_str else None
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.filter_queryset(self.get_queryset())

        analysis_data = []
        for stock in queryset:
            period_data = self._calculate_stock_for_period(stock, fy_start, fy_end, created_before)
            carryover = self._calculate_stock_before_period(stock, fy_start, created_before)
            stock_left = carryover + period_data["stock_in"] - period_data["stock_out"]

            analysis_data.append(
                {
                    "stock_id": stock.id,
                    "species": stock.species.id,
                    "species_name": stock.species.species_name,
                    "grade": stock.grade,
                    "stock_in": period_data["stock_in"],
                    "stock_out": period_data["stock_out"],
                    "stock_left": stock_left,
                    "carryover_from_previous_year": carryover,
                    "fiscal_year": fiscal_year,
                }
            )

        serializer = FiscalYearStockAnalysisSerializer(analysis_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticatedReadOnly])
    def fiscal_year_summary(self, request):
        """
        Get aggregated stock summary for a specific fiscal year.

        Query Parameters:
        - fiscal_year: Fiscal year in format YYYY/YY (e.g., 2082/83). Defaults to current fiscal year.
        - species: Filter by species ID (optional)
        - grade: Filter by grade (optional)
        - created_before: Only include transactions created before this date (YYYY-MM-DD or ISO format, optional)
        """
        fiscal_year = request.query_params.get("fiscal_year", SystemConfig.get().current_fiscal_year)
        created_before_str = request.query_params.get("created_before")

        try:
            fy_start, fy_end = self._get_fiscal_year_dates(fiscal_year)
            created_before = self._parse_created_before_date(created_before_str) if created_before_str else None
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.filter_queryset(self.get_queryset())

        total_stock_in = Decimal("0.00")
        total_stock_out = Decimal("0.00")
        total_carryover = Decimal("0.00")
        by_species = []

        for stock in queryset:
            period_data = self._calculate_stock_for_period(stock, fy_start, fy_end, created_before)
            carryover = self._calculate_stock_before_period(stock, fy_start, created_before)
            stock_left = carryover + period_data["stock_in"] - period_data["stock_out"]

            total_stock_in += period_data["stock_in"]
            total_stock_out += period_data["stock_out"]
            total_carryover += carryover

            by_species.append(
                {
                    "stock_id": stock.id,
                    "species": stock.species.id,
                    "species_name": stock.species.species_name,
                    "grade": stock.grade,
                    "stock_in": period_data["stock_in"],
                    "stock_out": period_data["stock_out"],
                    "stock_left": stock_left,
                    "carryover_from_previous_year": carryover,
                    "fiscal_year": fiscal_year,
                }
            )

        total_stock_left = total_carryover + total_stock_in - total_stock_out

        summary = {
            "fiscal_year": fiscal_year,
            "total_stock_in": total_stock_in,
            "total_stock_out": total_stock_out,
            "total_stock_left": total_stock_left,
            "total_carryover_from_previous_year": total_carryover,
            "by_species": by_species,
        }

        serializer = FiscalYearStockSummarySerializer(summary)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticatedReadOnly])
    def stock_in(self, request):
        """
        Get total stock in for a specific fiscal year.

        Query Parameters:
        - fiscal_year: Fiscal year in format YYYY/YY (e.g., 2082/83). Defaults to current fiscal year.
        - species: Filter by species ID (optional)
        - grade: Filter by grade (optional)
        - created_before: Only include transactions created before this date (YYYY-MM-DD or ISO format, optional)
        """
        fiscal_year = request.query_params.get("fiscal_year", SystemConfig.get().current_fiscal_year)
        created_before_str = request.query_params.get("created_before")

        try:
            fy_start, fy_end = self._get_fiscal_year_dates(fiscal_year)
            created_before = self._parse_created_before_date(created_before_str) if created_before_str else None
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.filter_queryset(self.get_queryset())

        total_stock_in = Decimal("0.00")
        by_species = []

        for stock in queryset:
            period_data = self._calculate_stock_for_period(stock, fy_start, fy_end, created_before)
            total_stock_in += period_data["stock_in"]

            by_species.append(
                {
                    "species": stock.species.id,
                    "species_name": stock.species.species_name,
                    "grade": stock.grade,
                    "stock_in": period_data["stock_in"],
                }
            )

        return Response(
            {
                "fiscal_year": fiscal_year,
                "total_stock_in": total_stock_in,
                "by_species": by_species,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticatedReadOnly])
    def stock_left(self, request):
        """
        Get total stock left (available) at the end of a specific fiscal year.

        Query Parameters:
        - fiscal_year: Fiscal year in format YYYY/YY (e.g., 2082/83). Defaults to current fiscal year.
        - species: Filter by species ID (optional)
        - grade: Filter by grade (optional)
        - created_before: Only include transactions created before this date (YYYY-MM-DD or ISO format, optional)
        """
        fiscal_year = request.query_params.get("fiscal_year", SystemConfig.get().current_fiscal_year)
        created_before_str = request.query_params.get("created_before")

        try:
            fy_start, fy_end = self._get_fiscal_year_dates(fiscal_year)
            created_before = self._parse_created_before_date(created_before_str) if created_before_str else None
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.filter_queryset(self.get_queryset())

        total_stock_left = Decimal("0.00")
        by_species = []

        for stock in queryset:
            period_data = self._calculate_stock_for_period(stock, fy_start, fy_end, created_before)
            carryover = self._calculate_stock_before_period(stock, fy_start, created_before)
            stock_left = carryover + period_data["stock_in"] - period_data["stock_out"]

            total_stock_left += stock_left

            by_species.append(
                {
                    "species": stock.species.id,
                    "species_name": stock.species.species_name,
                    "grade": stock.grade,
                    "stock_left": stock_left,
                }
            )

        return Response(
            {
                "fiscal_year": fiscal_year,
                "total_stock_left": total_stock_left,
                "by_species": by_species,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticatedReadOnly])
    def carryover_from_previous_year(self, request):
        """
        Get stock carried over from the previous fiscal year (opening stock).

        Query Parameters:
        - fiscal_year: Fiscal year in format YYYY/YY (e.g., 2082/83). Defaults to current fiscal year.
        - species: Filter by species ID (optional)
        - grade: Filter by grade (optional)
        - created_before: Only include transactions created before this date (YYYY-MM-DD or ISO format, optional)
        """
        fiscal_year = request.query_params.get("fiscal_year", SystemConfig.get().current_fiscal_year)
        created_before_str = request.query_params.get("created_before")

        try:
            fy_start, fy_end = self._get_fiscal_year_dates(fiscal_year)
            created_before = self._parse_created_before_date(created_before_str) if created_before_str else None
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.filter_queryset(self.get_queryset())

        total_carryover = Decimal("0.00")
        by_species = []

        for stock in queryset:
            carryover = self._calculate_stock_before_period(stock, fy_start, created_before)
            total_carryover += carryover

            by_species.append(
                {
                    "species": stock.species.id,
                    "species_name": stock.species.species_name,
                    "grade": stock.grade,
                    "carryover_from_previous_year": carryover,
                }
            )

        return Response(
            {
                "fiscal_year": fiscal_year,
                "total_carryover_from_previous_year": total_carryover,
                "by_species": by_species,
            },
            status=status.HTTP_200_OK,
        )


class StockTransactionViewSet(viewsets.ModelViewSet):
    queryset = StockTransaction.objects.select_related("stock")
    serializer_class = StockTransactionSerializer
    permission_classes = [IsCommitteeChair | IsAuthenticatedReadOnly]
    filterset_fields = ["stock", "transaction_type", "reference_type"]

    @action(detail=False, methods=["post"], permission_classes=[IsCommitteeChair])
    def record_adjustment(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        transaction = serializer.save(reference_type=StockTransaction.ReferenceType.ADJUSTMENT, reference_id=0)
        return Response(self.get_serializer(transaction).data, status=status.HTTP_201_CREATED)


class PriceRateViewSet(viewsets.ModelViewSet):
    queryset = PriceRate.objects.select_related("species")
    serializer_class = PriceRateSerializer
    permission_classes = [IsCommitteeChair | IsAuthenticatedReadOnly]
    filterset_fields = ["species", "grade", "buyer_type"]


class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.select_related("species", "member")
    serializer_class = SaleSerializer
    permission_classes = [IsCommitteeChair | IsAuthenticatedReadOnly]
    filterset_fields = ["buyer_type", "species", "grade", "payment_status"]
    search_fields = ["buyer_name", "member__full_name"]

    @action(detail=False, methods=["post"], permission_classes=[IsCommitteeChair])
    def record(self, request):
        from apps.core.services import record_sale

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        print(serializer.errors)
        try:
            sale = record_sale(serializer.validated_data, request.user)
        except ValueError as exc:
            raise ValidationError(str(exc))

        return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)


class TimberLogEntryViewSet(viewsets.ModelViewSet):
    queryset = TimberLogEntry.objects.select_related("species").all()
    serializer_class = TimberLogEntrySerializer
    filterset_fields = ["species", "grade"]
    search_fields = ["tree_no", "tree_golia_no", "golia_no"]
    ordering = ["-created_at"]
