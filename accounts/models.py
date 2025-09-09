from datetime import timedelta

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra):
        extra.setdefault("role", "ADMIN")
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(username, email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    role = models.CharField(max_length=10)  # 'ADMIN', 'OWNER' 등
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # admin 접근 여부

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    def __str__(self):
        return self.username


class UserProfile(models.Model):
    SUBSCRIPTION_CHOICES = [
        ("free", "무료"),
        ("premium", "프리미엄"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    subscription_type = models.CharField(
        max_length=10, choices=SUBSCRIPTION_CHOICES, default="free"
    )
    subscription_start = models.DateTimeField(null=True, blank=True)
    subscription_end = models.DateTimeField(null=True, blank=True)
    daily_usage_count = models.PositiveIntegerField(default=0)
    daily_usage_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_subscription_type_display()}"

    def is_premium(self):
        if self.subscription_type == "premium" and self.subscription_end:
            return timezone.now() <= self.subscription_end
        return False

    def can_use_service(self):
        # 프리미엄 사용자는 무제한
        if self.is_premium():
            return True

        # 무료 사용자는 일일 10회 제한
        today = timezone.now().date()
        if self.daily_usage_date != today:
            self.daily_usage_count = 0
            self.daily_usage_date = today
            self.save()

        return self.daily_usage_count < 10

    def increment_usage(self):
        today = timezone.now().date()
        if self.daily_usage_date != today:
            self.daily_usage_count = 0
            self.daily_usage_date = today

        self.daily_usage_count += 1
        self.save()


class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ("pending", "대기중"),
        ("completed", "완료"),
        ("failed", "실패"),
        ("cancelled", "취소"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")
    amount = models.PositiveIntegerField()  # 원 단위
    payment_key = models.CharField(max_length=200, unique=True)  # 토스 페이먼츠 결제키
    order_id = models.CharField(max_length=100, unique=True)  # 주문번호
    status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending"
    )
    subscription_months = models.PositiveIntegerField(default=1)  # 구독 개월 수
    payment_method = models.CharField(max_length=50, blank=True)  # 결제 방법
    approved_at = models.DateTimeField(null=True, blank=True)  # 승인 시간
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount}원 ({self.get_status_display()})"

    def activate_subscription(self):
        """결제 완료 시 사용자 구독 활성화"""
        if self.status == "completed":
            profile, created = UserProfile.objects.get_or_create(user=self.user)

            # 현재 프리미엄이면 연장, 아니면 새로 시작
            if profile.is_premium():
                start_date = profile.subscription_end
            else:
                start_date = timezone.now()

            profile.subscription_type = "premium"
            profile.subscription_start = start_date
            profile.subscription_end = start_date + timedelta(
                days=30 * self.subscription_months
            )
            profile.save()
