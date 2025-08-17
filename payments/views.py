import json
import uuid
import requests
from datetime import datetime, timedelta
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from accounts.models import User, UserProfile, Payment


# 토스 페이먼츠 설정
TOSS_CLIENT_KEY = "test_ck_D5GePWvyJnrK0W0k6q8gLzN97Eoq"  # 테스트 키
TOSS_SECRET_KEY = "test_sk_zXLkKEypNArWmo50nX3lmeaxYG5R"  # 테스트 키
TOSS_API_URL = "https://api.tosspayments.com/v1/payments"


@login_required
def payment_page(request):
    """결제 페이지"""
    plan = request.GET.get('plan', 'premium')
    extend = request.GET.get('extend', 'false') == 'true'
    
    context = {
        'plan': plan,
        'extend': extend,
        'user': request.user
    }
    
    return render(request, 'pages/payment.html', context)


@login_required
@require_http_methods(["POST"])
def create_order(request):
    """주문 생성 API"""
    try:
        data = json.loads(request.body)
        amount = data.get('amount')
        order_id = data.get('order_id')
        plan = data.get('plan', 'premium')
        
        # 주문 유효성 검사
        if not amount or not order_id:
            return JsonResponse({'success': False, 'message': '주문 정보가 부족합니다.'}, status=400)
        
        if amount != 9500:  # 프리미엄 플랜 가격
            return JsonResponse({'success': False, 'message': '잘못된 결제 금액입니다.'}, status=400)
        
        # 중복 주문 확인
        if Payment.objects.filter(order_id=order_id).exists():
            return JsonResponse({'success': False, 'message': '이미 존재하는 주문입니다.'}, status=400)
        
        # 결제 정보 저장
        payment = Payment.objects.create(
            user=request.user,
            amount=amount,
            payment_key='',  # 토스에서 생성될 예정
            order_id=order_id,
            status='pending',
            subscription_months=1
        )
        
        return JsonResponse({
            'success': True,
            'payment_id': payment.id,
            'order_id': order_id
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


def payment_success(request):
    """결제 성공 콜백"""
    payment_key = request.GET.get('paymentKey')
    order_id = request.GET.get('orderId')
    amount = request.GET.get('amount')
    
    if not all([payment_key, order_id, amount]):
        return render(request, 'pages/payment_result.html', {
            'success': False,
            'message': '결제 정보가 부족합니다.'
        })
    
    try:
        # 결제 승인 요청
        confirm_response = confirm_payment(payment_key, order_id, amount)
        
        if confirm_response['success']:
            # 결제 정보 업데이트
            payment = Payment.objects.get(order_id=order_id)
            payment.payment_key = payment_key
            payment.status = 'completed'
            payment.approved_at = timezone.now()
            payment.payment_method = confirm_response['data'].get('method', '')
            payment.save()
            
            # 구독 활성화
            payment.activate_subscription()
            
            return render(request, 'pages/payment_result.html', {
                'success': True,
                'payment': payment,
                'message': '결제가 성공적으로 완료되었습니다.'
            })
        else:
            return render(request, 'pages/payment_result.html', {
                'success': False,
                'message': confirm_response['message']
            })
            
    except Payment.DoesNotExist:
        return render(request, 'pages/payment_result.html', {
            'success': False,
            'message': '주문 정보를 찾을 수 없습니다.'
        })
    except Exception as e:
        return render(request, 'pages/payment_result.html', {
            'success': False,
            'message': f'결제 처리 중 오류가 발생했습니다: {str(e)}'
        })


def payment_fail(request):
    """결제 실패 콜백"""
    code = request.GET.get('code')
    message = request.GET.get('message')
    order_id = request.GET.get('orderId')
    
    try:
        if order_id:
            payment = Payment.objects.get(order_id=order_id)
            payment.status = 'failed'
            payment.save()
    except Payment.DoesNotExist:
        pass
    
    return render(request, 'pages/payment_result.html', {
        'success': False,
        'message': message or '결제가 취소되었습니다.',
        'code': code
    })


@csrf_exempt
@require_http_methods(["POST"])
def payment_webhook(request):
    """토스 페이먼츠 웹훅"""
    try:
        data = json.loads(request.body)
        event_type = data.get('eventType')
        payment_data = data.get('data', {})
        
        if event_type == 'PAYMENT_STATUS_CHANGED':
            payment_key = payment_data.get('paymentKey')
            order_id = payment_data.get('orderId')
            status = payment_data.get('status')
            
            try:
                payment = Payment.objects.get(order_id=order_id)
                
                if status == 'DONE':
                    payment.status = 'completed'
                    payment.approved_at = timezone.now()
                    payment.activate_subscription()
                elif status == 'CANCELED':
                    payment.status = 'cancelled'
                elif status == 'FAILED':
                    payment.status = 'failed'
                
                payment.save()
                
            except Payment.DoesNotExist:
                pass
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def confirm_payment(payment_key, order_id, amount):
    """토스 페이먼츠 결제 승인"""
    try:
        url = f"{TOSS_API_URL}/confirm"
        headers = {
            'Authorization': f'Basic {TOSS_SECRET_KEY}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'paymentKey': payment_key,
            'orderId': order_id,
            'amount': int(amount)
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            return {
                'success': True,
                'data': response.json()
            }
        else:
            error_data = response.json()
            return {
                'success': False,
                'message': error_data.get('message', '결제 승인에 실패했습니다.')
            }
            
    except Exception as e:
        return {
            'success': False,
            'message': f'결제 승인 요청 중 오류가 발생했습니다: {str(e)}'
        }


# 페이지 뷰들
def start_page(request):
    """무료 시작하기 페이지"""
    return render(request, 'pages/start.html')


def summary_page(request):
    """요약 피드 페이지"""
    from cafes.models import CafeId, CafeTrendAI
    from django.db.models import Count, Avg, Q
    from accounts.models import UserProfile
    
    # franchise_type 파라미터 가져오기
    franchise_type = request.GET.get('franchise_type')
    
    # 사용자 권한 확인 (로그인 필수)
    has_premium_access = False
    is_authenticated = request.user.is_authenticated
    
    if is_authenticated:
        # 관리자이거나 프리미엄 구독자인 경우
        if request.user.is_staff or request.user.is_superuser:
            has_premium_access = True
        else:
            try:
                profile = UserProfile.objects.get(user=request.user)
                has_premium_access = profile.is_premium()
            except UserProfile.DoesNotExist:
                has_premium_access = False
    
    # 기본 데이터
    total_cafes = CafeId.objects.count()
    new_cafes = 47  # 샘플 데이터
    risk_areas = 12  # 샘플 데이터
    avg_growth = 8.3  # 샘플 데이터
    
    # 프랜차이즈별 분석 데이터
    franchise_analysis = None
    if franchise_type:
        # 해당 프랜차이즈 카페들
        franchise_cafes = CafeId.objects.filter(franchise_type=franchise_type)
        franchise_count = franchise_cafes.count()
        
        if franchise_count > 0:
            # 해당 프랜차이즈의 지역별 분포
            location_distribution = franchise_cafes.values('address').annotate(
                count=Count('cafe_id')
            ).order_by('-count')[:5]
            
            # 해당 프랜차이즈 카페들의 rp_key로 트렌드 데이터 가져오기
            rp_keys = franchise_cafes.values_list('rp_key', flat=True)
            trend_data = CafeTrendAI.objects.filter(rp_key__in=rp_keys)
            
            # 트렌드 분석
            trend_stats = trend_data.aggregate(
                avg_growth_rate=Avg('predicted_growth_rate'),
                investment_opportunities=Count('trend_id', filter=Q(investment_opportunity=True)),
                risk_areas=Count('trend_id', filter=Q(is_risk_area=True)),
                trendy_count=Count('trend_id', filter=Q(is_trendy=True))
            )
            
            # 예상 월 매출 계산 (매장 수 기반)
            estimated_monthly_sales = franchise_count * 2800  # 만원 단위
            
            franchise_analysis = {
                'franchise_type': franchise_type,
                'total_count': franchise_count,
                'avg_growth_rate': round(trend_stats['avg_growth_rate'] or 0, 1),
                'investment_opportunities': trend_stats['investment_opportunities'],
                'risk_areas': trend_stats['risk_areas'],
                'trendy_count': trend_stats['trendy_count'],
                'location_distribution': location_distribution,
                'market_share': round((franchise_count / total_cafes) * 100, 1) if total_cafes > 0 else 0,
                'estimated_monthly_sales': estimated_monthly_sales,
                'roi_prediction': round(15.2 + (trend_stats['avg_growth_rate'] or 0) * 0.3, 1)  # ROI 예측값
            }
    
    context = {
        'today': timezone.now(),
        'total_cafes': total_cafes,
        'new_cafes': new_cafes,
        'risk_areas': risk_areas,
        'avg_growth': avg_growth,
        'franchise_analysis': franchise_analysis,
        'has_premium_access': has_premium_access,
        'is_authenticated': is_authenticated,
    }
    
    return render(request, 'pages/summary.html', context)


@login_required
def account_page(request):
    """내 계정 페이지"""
    # 사용자 프로필이 없으면 생성
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    context = {
        'user': request.user,
        'profile': profile
    }
    
    return render(request, 'pages/account.html', context)


@login_required
def usage_api(request):
    """사용량 조회 API"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    return JsonResponse({
        'success': True,
        'daily_usage': profile.daily_usage_count,
        'can_use': profile.can_use_service(),
        'is_premium': profile.is_premium()
    })