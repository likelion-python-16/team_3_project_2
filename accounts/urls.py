from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

app_name = 'accounts'

# Router for ViewSets (both API and template actions)
router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

# Manual URL patterns for simpler template access
template_patterns = [
    path('', UserViewSet.as_view({'get': 'template_list'}), name='user_list'),
    path('user/<int:pk>/', UserViewSet.as_view({'get': 'template_detail'}), name='user_detail'),
]

# Combine template patterns and router URLs
urlpatterns = template_patterns + router.urls
