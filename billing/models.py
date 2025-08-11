from django.db import models

class SubscriptionPlan(models.Model):
    plan_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=80)
    price = models.PositiveIntegerField()
    billing_cycle = models.CharField(max_length=10)  # 'monthly', 'annual'
    features_json = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.name} ({self.billing_cycle})"

class Subscription(models.Model):
    subscription_id = models.AutoField(primary_key=True)
    owner = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=10)  # 'active', 'canceled', ...
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)
    cancel_at = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Sub#{self.subscription_id} {self.owner} -> {self.plan}"

class Invoice(models.Model):
    invoice_id = models.AutoField(primary_key=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="invoices")
    period_start = models.DateField()
    period_end = models.DateField()
    amount_due = models.PositiveIntegerField()
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=10)  # 'issued', 'paid', 'void'
    due_date = models.DateField()
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice#{self.invoice_id} ({self.status})"

class PaymentProvider(models.Model):
    provider_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=80)
    method = models.CharField(max_length=20)  # 'card', 'bank_transfer', 'easy_pay'
    merchant_id = models.CharField(max_length=120)
    config_json = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.name} ({self.method})"

class Payment(models.Model):
    payment_id = models.AutoField(primary_key=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="payments")
    provider = models.ForeignKey(PaymentProvider, on_delete=models.PROTECT, related_name="payments")
    amount_paid = models.PositiveIntegerField()
    currency = models.CharField(max_length=3)
    external_txn_id = models.CharField(max_length=120)
    paid_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10)  # 'success', 'failed', 'pending'

    def __str__(self):
        return f"Payment#{self.payment_id} {self.status}"
