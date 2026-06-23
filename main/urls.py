"""
URL configuration for main project.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/core/", include("apps.core.urls")),
    path("api/v1/members/", include("apps.members.urls")),
    path("api/v1/forest/", include("apps.forest.urls")),
    path("api/v1/harvest/", include("apps.harvest.urls")),
    path("api/v1/inventory/", include("apps.inventory.urls")),
    path("api/v1/visitors/", include("apps.visitors.urls")),
    path("api/v1/billing/", include("apps.billing.urls")),
    path("api/v1/governance/", include("apps.governance.urls")),
    path("api/v1/fund/", include("apps.fund.urls")),
    path("api/v1/livelihood/", include("apps.livelihood.urls")),
    path("api/v1/offense/", include("apps.offense.urls")),
    path("api/v1/reports/", include("apps.reports.urls")),
]
