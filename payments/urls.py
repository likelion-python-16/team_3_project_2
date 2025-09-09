from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    # 페이지 뷰
    path("start/", views.start_page, name="start"),
    path("summary/", views.summary_page, name="summary"),
    path("account/", views.account_page, name="account"),
    path("payment/", views.payment_page, name="payment"),
    path("success/", views.success_page, name="success"),
    path("fail/", views.fail_page, name="fail"),
    # 사용자 관련 API
    path("api/accounts/usage/", views.usage_api, name="usage_api"),
    path("api/payment/success/", views.payment_success_api, name="payment_success_api"),
]
