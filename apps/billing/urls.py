from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.billing.views import FeeCollectionViewSet, ReceiptViewSet

router = DefaultRouter()
router.register(r"receipts", ReceiptViewSet)
router.register(r"fee-collections", FeeCollectionViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
