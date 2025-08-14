from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from accounts.views import login_page
from cafes.views import CafeIdViewSet

urlpatterns = [
    path("", include(('cafes.urls', 'cafes'), namespace='cafes-web')),
    path("login/", login_page, name="login"),
    path('admin/', admin.site.urls),
    
    
    # Template-based URLs
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts-web')),
    path('billing/', include(('billing.urls', 'billing'), namespace='billing-web')),
    path('cafes/', include(('cafes.urls', 'cafes'), namespace='cafes-web')),
    
    # API URLs
    path('api/accounts/', include(('accounts.urls', 'accounts'), namespace='accounts-api')),
    path('api/billing/', include(('billing.urls', 'billing'), namespace='billing-api')),
    path('api/cafes/', include(('cafes.urls', 'cafes'), namespace='cafes-api')),
    path("api-auth/", include("rest_framework.urls")),
]
