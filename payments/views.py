import json
import uuid
import requests
import base64
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
from django.db import IntegrityError
from accounts.models import User, UserProfile, Payment


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
            location_distribution = franchise_cafes.values('distinct').annotate(
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
    
    # 결제 내역을 최신순으로 정렬하여 가져오기
    payments = request.user.payments.all().order_by('-created_at')
    
    context = {
        'user': request.user,
        'profile': profile,
        'payments': payments
    }
    
    return render(request, 'pages/account.html', context)


def success_page(request):
    """결제 성공 페이지"""
    return render(request, 'pages/success.html')


def fail_page(request):
    """결제 실패 페이지"""
    return render(request, 'pages/fail.html')


@csrf_exempt
@require_http_methods(["POST"])
def payment_success_api(request):
    """결제 성공 처리 API"""
    print(f"[DEBUG] API 호출 시작 - User authenticated: {request.user.is_authenticated}")
    print(f"[DEBUG] Request body: {request.body}")
    
    try:
        data = json.loads(request.body)
        payment_key = data.get('paymentKey')
        order_id = data.get('orderId')
        amount = data.get('amount')
        
        print(f"[DEBUG] 파라미터 추출 - paymentKey: {payment_key}, orderId: {order_id}, amount: {amount}")
        
        if not payment_key or not order_id or not amount:
            missing_params = []
            if not payment_key: missing_params.append('paymentKey')
            if not order_id: missing_params.append('orderId')
            if not amount: missing_params.append('amount')
            
            error_msg = f'필수 파라미터가 누락되었습니다: {", ".join(missing_params)}'
            print(f"[DEBUG] {error_msg}")
            return JsonResponse({
                'success': False,
                'error': error_msg
            }, status=400)
        
        amount = int(amount)
        
        # 토스 페이먼츠 API로 결제 검증 (테스트 환경에서는 생략)
        payment_method = "테스트결제"  # 기본값
        
        # 테스트 키인지 확인 (실제 운영환경에서는 이 부분을 제거하고 항상 검증해야 함)
        if payment_key.startswith('tgen_'):
            print(f"[DEBUG] 테스트 결제로 인식 - 토스 API 검증 생략")
            # 테스트 환경에서는 검증 생략
            payment_data = {
                'method': '테스트결제',
                'orderId': order_id,
                'totalAmount': amount
            }
        else:
            # 실제 결제일 경우 토스 API 검증
            print(f"[DEBUG] 실제 결제 - 토스 API 검증 시작")
            toss_secret_key = "test_sk_6BYq7GWPVvxKzQ7Dq0qm8NE5vbo1"
            auth_string = base64.b64encode(f"{toss_secret_key}:".encode()).decode()
            
            headers = {
                'Authorization': f'Basic {auth_string}',
                'Content-Type': 'application/json'
            }
            
            verify_url = f"https://api.tosspayments.com/v1/payments/{payment_key}"
            response = requests.get(verify_url, headers=headers)
            
            if response.status_code != 200:
                print(f"[DEBUG] 토스 API 응답 오류: {response.status_code}, {response.text}")
                return JsonResponse({
                    'success': False,
                    'error': f'결제 검증에 실패했습니다. 상태코드: {response.status_code}'
                }, status=400)
            
            payment_data = response.json()
            
            # 결제 정보 검증
            if payment_data['orderId'] != order_id or payment_data['totalAmount'] != amount:
                print(f"[DEBUG] 결제 정보 불일치 - API orderId: {payment_data['orderId']}, 요청 orderId: {order_id}")
                print(f"[DEBUG] 결제 정보 불일치 - API amount: {payment_data['totalAmount']}, 요청 amount: {amount}")
                return JsonResponse({
                    'success': False,
                    'error': '결제 정보가 일치하지 않습니다.'
                }, status=400)
        
        # orderId에서 user_id 추출 (order_userid_timestamp_random 형태)
        user = None
        try:
            # orderId 파싱: order_userid_timestamp_random
            order_parts = order_id.split('_')
            if len(order_parts) >= 4 and order_parts[0] == 'order':
                user_id = int(order_parts[1])
                user = User.objects.get(user_id=user_id)
                print(f"[DEBUG] orderId에서 추출한 user_id: {user_id}, user: {user}")
            else:
                # 기존 형식 (order_timestamp_random) - 로그인된 사용자 사용
                if request.user.is_authenticated:
                    user = request.user
                    print(f"[DEBUG] 로그인된 사용자 사용: {user}")
                else:
                    print(f"[DEBUG] orderId 파싱 실패 및 비로그인 상태: {order_id}")
        except (ValueError, User.DoesNotExist) as e:
            print(f"[DEBUG] 사용자 추출 오류: {e}")
            
        if not user:
            return JsonResponse({
                'success': False,
                'error': f'사용자를 찾을 수 없습니다. orderId: {order_id}'
            }, status=400)
        
        # 중복 결제 확인
        existing_payment = Payment.objects.filter(
            payment_key=payment_key
        ).first()
        
        if existing_payment:
            return JsonResponse({
                'success': False,
                'error': '이미 처리된 결제입니다.'
            }, status=400)
        
        # orderName에서 구독 개월 수 추출
        order_name = payment_data.get('orderName', '')
        subscription_months = 1  # 기본값
        
        try:
            if '1개월' in order_name:
                subscription_months = 1
            elif '6개월' in order_name:
                subscription_months = 6
            elif '12개월' in order_name:
                subscription_months = 12
            else:
                # 정규표현식으로 숫자 추출 시도
                import re
                match = re.search(r'(\d+)개월', order_name)
                if match:
                    subscription_months = int(match.group(1))
        except Exception as e:
            print(f"[DEBUG] 구독 개월 수 추출 오류: {e}, orderName: {order_name}")
            subscription_months = 1
        
        print(f"[DEBUG] 추출된 구독 개월 수: {subscription_months}, orderName: {order_name}")
        
        # Payment 모델에 저장
        print(f"[DEBUG] Payment 모델 저장 시작 - user: {user}, amount: {amount}")
        
        payment = Payment.objects.create(
            user=user,
            amount=amount,
            payment_key=payment_key,
            order_id=order_id,
            status='completed',
            subscription_months=subscription_months,
            payment_method=payment_data.get('method', ''),
            approved_at=timezone.now()
        )
        
        print(f"[DEBUG] Payment 저장 완료 - payment_id: {payment.id}")
        
        # 구독 활성화
        payment.activate_subscription()
        print(f"[DEBUG] 구독 활성화 완료")
        
        return JsonResponse({
            'success': True,
            'payment_id': payment.id,
            'user_id': user.user_id,
            'message': '결제가 성공적으로 처리되었습니다.'
        })
        
    except json.JSONDecodeError as e:
        print(f"[DEBUG] JSON 파싱 오류: {e}")
        return JsonResponse({
            'success': False,
            'error': '잘못된 요청 형식입니다.'
        }, status=400)
    except Exception as e:
        print(f"[DEBUG] 예외 발생: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'서버 오류가 발생했습니다: {str(e)}'
        }, status=500)


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