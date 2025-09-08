from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from .models import User, UserProfile, Payment

class UserModelTest(TestCase):
    def test_create_user(self):
        """일반 유저 생성 테스트"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('password123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """슈퍼유저 생성 테스트"""
        admin_user = User.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='password123'
        )
        self.assertEqual(admin_user.username, 'adminuser')
        self.assertEqual(admin_user.email, 'admin@example.com')
        self.assertTrue(admin_user.check_password('password123'))
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertEqual(admin_user.role, 'ADMIN')

class UserProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com')
        self.profile = UserProfile.objects.get(user=self.user)

    def test_default_subscription(self):
        """기본 구독 상태가 'free'인지 테스트"""
        self.assertEqual(self.profile.subscription_type, 'free')
        self.assertFalse(self.profile.is_premium())

    def test_premium_status(self):
        """프리미엄 상태가 정확하게 계산되는지 테스트"""
        # 구독 만료일이 없는 경우
        self.profile.subscription_type = 'premium'
        self.profile.subscription_end = None
        self.assertFalse(self.profile.is_premium())

        # 구독 기간이 유효한 경우
        self.profile.subscription_end = timezone.now() + timedelta(days=1)
        self.assertTrue(self.profile.is_premium())

        # 구독 기간이 만료된 경우
        self.profile.subscription_end = timezone.now() - timedelta(days=1)
        self.assertFalse(self.profile.is_premium())

    def test_can_use_service_free_user(self):
        """무료 사용자의 서비스 이용 제한 테스트"""
        self.profile.daily_usage_count = 9
        self.assertTrue(self.profile.can_use_service())

        self.profile.daily_usage_count = 10
        self.assertFalse(self.profile.can_use_service())

    def test_can_use_service_premium_user(self):
        """프리미엄 사용자는 무제한 이용 가능한지 테스트"""
        self.profile.subscription_type = 'premium'
        self.profile.subscription_end = timezone.now() + timedelta(days=30)
        self.profile.daily_usage_count = 100 # 10회 이상
        self.assertTrue(self.profile.can_use_service())

    def test_increment_usage(self):
        """사용량 증가 메서드 테스트"""
        self.profile.increment_usage()
        self.assertEqual(self.profile.daily_usage_count, 1)
        
        # 날짜가 바뀌면 초기화되는지 테스트
        self.profile.daily_usage_date = timezone.now().date() - timedelta(days=1)
        self.profile.save()
        self.profile.increment_usage()
        self.assertEqual(self.profile.daily_usage_count, 1)
        self.assertEqual(self.profile.daily_usage_date, timezone.now().date())

class PaymentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com')
        self.payment = Payment.objects.create(
            user=self.user,
            amount=5000,
            payment_key='test_payment_key',
            order_id='test_order_id',
            status='completed',
            subscription_months=1
        )

    def test_activate_subscription_new_premium(self):
        """신규 프리미엄 구독 활성화 테스트"""
        self.payment.activate_subscription()
        
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.subscription_type, 'premium')
        self.assertTrue(profile.is_premium())
        self.assertAlmostEqual(
            profile.subscription_end,
            timezone.now() + timedelta(days=30),
            delta=timedelta(seconds=10)
        )

    def test_activate_subscription_extend_premium(self):
        """기존 프리미엄 구독 연장 테스트"""
        profile = UserProfile.objects.get(user=self.user)
        initial_end_date = timezone.now() + timedelta(days=15)
        profile.subscription_type = 'premium'
        profile.subscription_end = initial_end_date
        profile.save()

        self.payment.activate_subscription()
        
        profile.refresh_from_db()
        self.assertEqual(profile.subscription_type, 'premium')
        self.assertAlmostEqual(
            profile.subscription_end,
            initial_end_date + timedelta(days=30),
            delta=timedelta(seconds=10)
        )
