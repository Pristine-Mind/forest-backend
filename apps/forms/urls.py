from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CuttingRegisterItemViewSet,
    CuttingRegisterViewSet,
    TreeSurveyFormItemViewSet,
    TreeSurveyFormViewSet,
)

router = DefaultRouter()
router.register(r"survey-forms", TreeSurveyFormViewSet, basename="survey-form")
router.register(r"survey-form-items", TreeSurveyFormItemViewSet, basename="survey-form-item")
router.register(r"cutting-registers", CuttingRegisterViewSet, basename="cutting-register")
router.register(r"cutting-register-items", CuttingRegisterItemViewSet, basename="cutting-register-item")

urlpatterns = [
    path("", include(router.urls)),
]
