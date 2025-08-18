from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (CafeIdViewSet, 
    pane_map_view, pane_franchise_view, pane_trend_view, pane_report_view
)

app_name = 'cafes'

# Router for ViewSets (both API and template actions)


# Manual URL patterns for simpler template access
template_patterns = [
    path('', CafeIdViewSet.as_view({'get': 'template_list'}), name='cafe_list'),
    
    path('pane/map/', pane_map_view, name='pane_map'),
    path('pane/franchise/', pane_franchise_view, name='pane_franchise'),
    path('pane/trend/', pane_trend_view, name='pane_trend'),
    path('pane/report/', pane_report_view, name='pane_report'),
]

# Combine template patterns and router URLs
urlpatterns = template_patterns 
