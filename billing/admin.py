from django.contrib import admin
from .models import SubscriptionPlan, Subscription, Invoice, PaymentProvider, Payment

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("plan_id", "name", "price", "billing_cycle")
    search_fields = ("name",)
    list_filter = ("billing_cycle",)
    ordering = ("plan_id",)

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("subscription_id", "owner", "plan", "status", "start_date", "end_date", "auto_renew")
    list_filter = ("status", "auto_renew")
    search_fields = ("owner__email", "owner__username")
    autocomplete_fields = ("owner", "plan")
    date_hierarchy = "start_date"
    ordering = ("-subscription_id",)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_id", "subscription", "amount_due", "currency", "status", "due_date", "issued_at")
    list_filter = ("status", "currency")
    search_fields = ("invoice_id", "subscription__owner__email")
    autocomplete_fields = ("subscription",)
    date_hierarchy = "issued_at"
    ordering = ("-issued_at",)

@admin.register(PaymentProvider)
class PaymentProviderAdmin(admin.ModelAdmin):
    list_display = ("provider_id", "name", "method", "merchant_id")
    list_filter = ("method",)
    search_fields = ("name", "merchant_id")
    ordering = ("name",)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("payment_id", "invoice", "provider", "amount_paid", "currency", "status", "paid_at")
    list_filter = ("status", "currency", "provider")
    search_fields = ("external_txn_id",)
    autocomplete_fields = ("invoice", "provider")
    date_hierarchy = "paid_at"
    ordering = ("-payment_id",)
