from rest_framework.routers import DefaultRouter
from .views import (
    SubscriptionPlanViewSet, SubscriptionViewSet, InvoiceViewSet,
    PaymentProviderViewSet, PaymentViewSet
)

router = DefaultRouter()
router.register(r"plans", SubscriptionPlanViewSet, basename="plan")
router.register(r"subscriptions", SubscriptionViewSet, basename="subscription")
router.register(r"invoices", InvoiceViewSet, basename="invoice")
router.register(r"payment-providers", PaymentProviderViewSet, basename="payment-provider")
router.register(r"payments", PaymentViewSet, basename="payment")

urlpatterns = router.urls
