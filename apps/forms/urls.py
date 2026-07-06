from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CuttingRegisterItemViewSet,
    CuttingRegisterViewSet,
    FellingRegisterEntryViewSet,
    FellingRegisterViewSet,
    ForestProductReceiptViewSet,
    TreeSurveyFormItemViewSet,
    TreeSurveyFormViewSet,
)

router = DefaultRouter()
router.register(r"survey-forms", TreeSurveyFormViewSet, basename="survey-form")
router.register(r"survey-form-items", TreeSurveyFormItemViewSet, basename="survey-form-item")
router.register(r"cutting-registers", CuttingRegisterViewSet, basename="cutting-register")
router.register(r"cutting-register-items", CuttingRegisterItemViewSet, basename="cutting-register-item")
router.register(r"felling-registers", FellingRegisterViewSet, basename="felling-register")
router.register(r"felling-register-entries", FellingRegisterEntryViewSet, basename="felling-register-entry")
router.register(r"forest-product-receipts", ForestProductReceiptViewSet, basename="forest-product-receipt")


urlpatterns = [
    path("", include(router.urls)),
]
