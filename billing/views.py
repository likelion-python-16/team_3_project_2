from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render
from .models import SubscriptionPlan, Subscription, Invoice, PaymentProvider, Payment
from .serializers import (
    SubscriptionPlanSerializer, SubscriptionSerializer, InvoiceSerializer,
    PaymentProviderSerializer, PaymentSerializer
)

class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    queryset = SubscriptionPlan.objects.all().order_by("plan_id")
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['get'])
    def template_list(self, request):
        plans = self.get_queryset()
        context = {'plans': plans}
        return render(request, 'billing/subscription_plan_list.html', context)
    
    @action(detail=True, methods=['get'])
    def template_detail(self, request, pk=None):
        plan = self.get_object()
        context = {'plan': plan}
        return render(request, 'billing/subscription_plan_detail.html', context)

class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.select_related("owner", "plan").order_by("-subscription_id")
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['get'])
    def template_list(self, request):
        subscriptions = self.get_queryset()
        context = {'subscriptions': subscriptions}
        return render(request, 'billing/subscription_list.html', context)
    
    @action(detail=True, methods=['get'])
    def template_detail(self, request, pk=None):
        subscription = self.get_object()
        context = {'subscription': subscription}
        return render(request, 'billing/subscription_detail.html', context)

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.select_related("subscription").order_by("-issued_at")
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['get'])
    def template_list(self, request):
        invoices = self.get_queryset()
        context = {'invoices': invoices}
        return render(request, 'billing/invoice_list.html', context)
    
    @action(detail=True, methods=['get'])
    def template_detail(self, request, pk=None):
        invoice = self.get_object()
        context = {'invoice': invoice}
        return render(request, 'billing/invoice_detail.html', context)

class PaymentProviderViewSet(viewsets.ModelViewSet):
    queryset = PaymentProvider.objects.all().order_by("name")
    serializer_class = PaymentProviderSerializer
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['get'])
    def template_list(self, request):
        providers = self.get_queryset()
        context = {'providers': providers}
        return render(request, 'billing/payment_provider_list.html', context)

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related("invoice", "provider").order_by("-payment_id")
    serializer_class = PaymentSerializer
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['get'])
    def template_list(self, request):
        payments = self.get_queryset()
        context = {'payments': payments}
        return render(request, 'billing/payment_list.html', context)
