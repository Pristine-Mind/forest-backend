from django.urls import path

from apps.reports.views import ReportsViewSet

urlpatterns = [
    path("tree-count/", ReportsViewSet.as_view({"get": "tree_count"}), name="report-tree-count"),
    path("harvest/", ReportsViewSet.as_view({"get": "harvest"}), name="report-harvest"),
    path("stock-register/", ReportsViewSet.as_view({"get": "stock_register"}), name="report-stock-register"),
    path("sales/", ReportsViewSet.as_view({"get": "sales"}), name="report-sales"),
    path("visitor-entries/", ReportsViewSet.as_view({"get": "visitor_entries"}), name="report-visitor-entries"),
    path("fund-audit/", ReportsViewSet.as_view({"get": "fund_audit"}), name="report-fund-audit"),
    path("governance/", ReportsViewSet.as_view({"get": "governance"}), name="report-governance"),
    path("livelihood/", ReportsViewSet.as_view({"get": "livelihood"}), name="report-livelihood"),
    path("offense/", ReportsViewSet.as_view({"get": "offense"}), name="report-offense"),
    path("annual-dfo/", ReportsViewSet.as_view({"get": "annual_dfo"}), name="report-annual-dfo"),
]
