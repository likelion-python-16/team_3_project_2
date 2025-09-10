import json
from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Payment, User, UserProfile


class PaymentViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.profile, created = UserProfile.objects.get_or_create(user=self.user)
        self.client.login(email="test@example.com", password="password123")

    def test_payment_page_loads_correctly(self):
        """/payment/ 페이지가 정상적으로 로드되는지 테스트"""
        response = self.client.get(reverse("payments:payment"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/payment.html")

    def test_summary_page_loads_correctly(self):
        """/summary/ 페이지가 정상적으로 로드되는지 테스트"""
        response = self.client.get(reverse("payments:summary"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/summary.html")

    def test_account_page_loads_correctly(self):
        """/account/ 페이지가 정상적으로 로드되는지 테스트"""
        response = self.client.get(reverse("payments:account"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/account.html")
        self.assertEqual(response.context["profile"], self.profile)

    @patch("payments.views.requests.get")
    def test_payment_success_api_with_test_key(self, mock_requests_get):
        """payment_success_api 테스트 (테스트 결제 키)"""
        url = reverse("payments:payment_success_api")
        order_id = f"order_{self.user.user_id}_{timezone.now().timestamp()}"
        data = {
            "paymentKey": "tgen_test_key",
            "orderId": order_id,
            "amount": 5000,
        }

        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertTrue(json_response["success"])
        self.assertEqual(json_response["user_id"], self.user.user_id)

        # DB에 Payment가 생성되었는지 확인
        self.assertTrue(
            Payment.objects.filter(order_id=order_id, status="completed").exists()
        )

        # UserProfile이 premium으로 변경되었는지 확인
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.is_premium())

    def test_payment_success_api_missing_params(self):
        """payment_success_api 필수 파라미터 누락 테스트"""
        url = reverse("payments:payment_success_api")
        data = {"orderId": "some_order_id"}  # paymentKey, amount 누락

        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        json_response = response.json()
        self.assertFalse(json_response["success"])
        self.assertIn("필수 파라미터가 누락되었습니다", json_response["error"])

    def test_usage_api(self):
        """usage_api가 정확한 사용량 정보를 반환하는지 테스트"""
        url = reverse("payments:usage_api")

        # 초기 사용량
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertTrue(json_response["success"])
        self.assertEqual(json_response["daily_usage"], 0)
        self.assertTrue(json_response["can_use"])

        # 사용량 증가
        self.profile.increment_usage()

        response = self.client.get(url)
        json_response = response.json()
        self.assertEqual(json_response["daily_usage"], 1)
