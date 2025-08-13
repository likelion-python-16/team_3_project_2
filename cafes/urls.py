from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    ResidentPopulationViewSet, CafeIdViewSet, CafeSalesViewSet,
    CafeReviewViewSet, CafeTrendAIViewSet
)

app_name = 'cafes'

# Router for ViewSets (both API and template actions)
router = DefaultRouter()
router.register(r"resident-populations", ResidentPopulationViewSet, basename="resident-population")
router.register(r"cafes", CafeIdViewSet, basename="cafe")
router.register(r"sales", CafeSalesViewSet, basename="cafe-sales")
router.register(r"reviews", CafeReviewViewSet, basename="cafe-review")
router.register(r"trends", CafeTrendAIViewSet, basename="cafe-trend")

# Manual URL patterns for simpler template access
template_patterns = [
    path('', CafeIdViewSet.as_view({'get': 'template_list'}), name='cafe_list'),
    path('cafe/<int:pk>/', CafeIdViewSet.as_view({'get': 'template_detail'}), name='cafe_detail'),
    path('sales/', CafeSalesViewSet.as_view({'get': 'template_list'}), name='cafe_sales_list'),
    path('reviews/', CafeReviewViewSet.as_view({'get': 'template_list'}), name='cafe_review_list'),
    path('populations/', ResidentPopulationViewSet.as_view({'get': 'template_list'}), name='resident_population_list'),
    path('trends/', CafeTrendAIViewSet.as_view({'get': 'template_list'}), name='cafe_trend_list'),
]

# Combine template patterns and router URLs
urlpatterns = template_patterns + router.urls
