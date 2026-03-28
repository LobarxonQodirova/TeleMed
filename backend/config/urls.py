"""Root URL configuration for TeleMed."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls", namespace="accounts")),
    path("api/consultations/", include("apps.consultations.urls", namespace="consultations")),
    path("api/appointments/", include("apps.appointments.urls", namespace="appointments")),
    path("api/prescriptions/", include("apps.prescriptions.urls", namespace="prescriptions")),
    path("api/payments/", include("apps.payments.urls", namespace="payments")),
    path("api/reviews/", include("apps.reviews.urls", namespace="reviews")),
    path("api/medical-files/", include("apps.medical_files.urls", namespace="medical_files")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
