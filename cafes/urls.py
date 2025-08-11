from rest_framework.routers import DefaultRouter
from .views import (
    ResidentPopulationViewSet, CafeIfViewSet, CafeSalesViewSet,
    CafeReviewViewSet, CafeTrendAIViewSet
)

router = DefaultRouter()
router.register(r"resident-populations", ResidentPopulationViewSet, basename="resident-population")
router.register(r"cafes", CafeIfViewSet, basename="cafe")
router.register(r"sales", CafeSalesViewSet, basename="cafe-sales")
router.register(r"reviews", CafeReviewViewSet, basename="cafe-review")
router.register(r"trends", CafeTrendAIViewSet, basename="cafe-trend")

urlpatterns = router.urls
