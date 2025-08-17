from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # 페이지 뷰
    path('start/', views.start_page, name='start'),
    path('summary/', views.summary_page, name='summary'),
    path('account/', views.account_page, name='account'),
    path('payment/', views.payment_page, name='payment'),
    
    # 결제 관련 API
    path('api/payments/create-order/', views.create_order, name='create_order'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/fail/', views.payment_fail, name='payment_fail'),
    path('api/payments/webhook/', views.payment_webhook, name='payment_webhook'),
    
    # 사용자 관련 API
    path('api/accounts/usage/', views.usage_api, name='usage_api'),
]