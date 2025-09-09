from rest_framework.routers import DefaultRouter

from .views import UserViewSet

app_name = "accounts"

# Router for ViewSets (both API and template actions)
router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

# API URLs only
urlpatterns = router.urls
