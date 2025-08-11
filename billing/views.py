from rest_framework import viewsets, permissions
from .models import SubscriptionPlan, Subscription, Invoice, PaymentProvider, Payment
from .serializers import (
    SubscriptionPlanSerializer, SubscriptionSerializer, InvoiceSerializer,
    PaymentProviderSerializer, PaymentSerializer
)

class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    queryset = SubscriptionPlan.objects.all().order_by("plan_id")
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]

class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.select_related("owner", "plan").order_by("-subscription_id")
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.AllowAny]

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.select_related("subscription").order_by("-issued_at")
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.AllowAny]

class PaymentProviderViewSet(viewsets.ModelViewSet):
    queryset = PaymentProvider.objects.all().order_by("name")
    serializer_class = PaymentProviderSerializer
    permission_classes = [permissions.AllowAny]

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related("invoice", "provider").order_by("-payment_id")
    serializer_class = PaymentSerializer
    permission_classes = [permissions.AllowAny]
