from django.contrib import admin
from django.urls import include, path

from accounts.views import login_page, register_page

urlpatterns = [
    path("", include(("cafes.urls", "cafes"), namespace="cafes-main")),
    path("login/", login_page, name="login"),
    path("register/", register_page, name="register"),
    path("admin/", admin.site.urls),
    # Payment and Pages URLs
    path("", include("payments.urls")),
    # Template-based URLs
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts-web")),
    path("cafes/", include(("cafes.urls", "cafes"), namespace="cafes-web")),
    # API URLs
    path(
        "api/accounts/",
        include(("accounts.urls", "accounts"), namespace="accounts-api"),
    ),
    path("api/cafes/", include(("cafes.urls", "cafes"), namespace="cafes-api")),
    path("metrics/", include("django_prometheus.urls")),
    path("api-auth/", include("rest_framework.urls")),
]
