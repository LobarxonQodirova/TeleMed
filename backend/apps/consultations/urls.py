"""URL configuration for consultations app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "consultations"

router = DefaultRouter()
router.register(r"", views.ConsultationViewSet, basename="consultation")

urlpatterns = [
    path(
        "<uuid:consultation_id>/notes/",
        views.ConsultationNoteViewSet.as_view({"get": "list", "post": "create"}),
        name="consultation-notes",
    ),
    path(
        "<uuid:consultation_id>/notes/<uuid:pk>/",
        views.ConsultationNoteViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="consultation-note-detail",
    ),
    path(
        "<uuid:consultation_id>/files/",
        views.ConsultationFileViewSet.as_view({"get": "list", "post": "create"}),
        name="consultation-files",
    ),
    path(
        "<uuid:consultation_id>/files/<uuid:pk>/",
        views.ConsultationFileViewSet.as_view({"get": "retrieve", "delete": "destroy"}),
        name="consultation-file-detail",
    ),
    path("", include(router.urls)),
]
