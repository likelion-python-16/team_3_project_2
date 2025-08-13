from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    SubscriptionPlanViewSet, SubscriptionViewSet, InvoiceViewSet,
    PaymentProviderViewSet, PaymentViewSet
)

app_name = 'billing'

# Router for ViewSets (both API and template actions)
router = DefaultRouter()
router.register(r"plans", SubscriptionPlanViewSet, basename="plan")
router.register(r"subscriptions", SubscriptionViewSet, basename="subscription")
router.register(r"invoices", InvoiceViewSet, basename="invoice")
router.register(r"payment-providers", PaymentProviderViewSet, basename="payment-provider")
router.register(r"payments", PaymentViewSet, basename="payment")

# Manual URL patterns for simpler template access
template_patterns = [
    path('', SubscriptionPlanViewSet.as_view({'get': 'template_list'}), name='subscription_plan_list'),
    path('plan/<int:pk>/', SubscriptionPlanViewSet.as_view({'get': 'template_detail'}), name='plan_detail'),
    path('subscriptions/', SubscriptionViewSet.as_view({'get': 'template_list'}), name='subscription_list'),
    path('subscription/<int:pk>/', SubscriptionViewSet.as_view({'get': 'template_detail'}), name='subscription_detail'),
    path('invoices/', InvoiceViewSet.as_view({'get': 'template_list'}), name='invoice_list'),
    path('invoice/<int:pk>/', InvoiceViewSet.as_view({'get': 'template_detail'}), name='invoice_detail'),
    path('providers/', PaymentProviderViewSet.as_view({'get': 'template_list'}), name='payment_provider_list'),
    path('payments/', PaymentViewSet.as_view({'get': 'template_list'}), name='payment_list'),
]

# Combine template patterns and router URLs
urlpatterns = template_patterns + router.urls
