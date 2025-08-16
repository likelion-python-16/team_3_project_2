from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render
from django.db.models import Q
from .models import ResidentPopulation, CafeId, CafeSales, CafeReview, CafeTrendAI
from .serializers import (
    ResidentPopulationSerializer, CafeIdSerializer, CafeSalesSerializer,
    CafeReviewSerializer, CafeTrendAISerializer
)
# 인구수
class ResidentPopulationViewSet(viewsets.ModelViewSet):
    queryset = ResidentPopulation.objects.all().order_by("rp_key")
    serializer_class = ResidentPopulationSerializer
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['get'])
    def template_list(self, request):
        populations = self.get_queryset()
        context = {'populations': populations}
        return render(request, 'cafes/resident_population_list.html', context)

class CafeIdViewSet(viewsets.ModelViewSet):
    queryset = CafeId.objects.select_related("rp_key").order_by("name")
    serializer_class = CafeIdSerializer
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['get'])
    def template_list(self, request):
        cafes = self.get_queryset()
        context = {'cafes': cafes}
        return render(request, 'index.html', context)
    
    @action(detail=True, methods=['get'])
    def template_detail(self, request, pk=None):
        cafe = self.get_object()
        context = {'cafe': cafe}
        return render(request, 'cafes/cafe_detail.html', context)
    
    @action(detail=False, methods=['get'])
    def filtered_data(self, request):
        """필터링된 카페 데이터를 반환하는 API - 인증 필요"""
        if not request.user.is_authenticated:
            return Response({
                'success': False,
                'message': '로그인이 필요한 서비스입니다.',
                'require_login': True
            }, status=401)
        
        queryset = self.get_queryset()
        
        # 지역 필터
        region = request.query_params.get('region')
        if region and region != '전체':
            queryset = queryset.filter(address__icontains=region)
        
        # 업종 대분류 필터
        major_category = request.query_params.get('major_category')
        if major_category and major_category not in ['전체', '']:
            # 업종 대분류에 따른 필터링 (예시)
            if major_category == '외식':
                queryset = queryset.filter(Q(name__icontains='카페') | Q(name__icontains='커피'))
        
        # 업종 중분류 필터
        mid_category = request.query_params.get('mid_category')
        if mid_category and mid_category not in ['전체', '']:
            if mid_category == '카페':
                queryset = queryset.filter(Q(name__icontains='카페') | Q(name__icontains='커피'))
            elif mid_category == '디저트':
                queryset = queryset.filter(Q(name__icontains='디저트') | Q(name__icontains='베이커리'))
        
        # 프랜차이즈 필터
        franchise = request.query_params.get('franchise')
        if franchise:
            queryset = queryset.filter(name__icontains=franchise)
        
        # 지도용 데이터 포맷
        map_data = []
        for cafe in queryset:
            map_data.append({
                'id': cafe.cafe_id,
                'name': cafe.name,
                'address': cafe.address,
                'latitude': cafe.latitude,
                'longitude': cafe.longitude,
                'status': self._get_cafe_status(cafe),  # 안정/주의/위험 상태
                'business_code': cafe.biz_code,
                'population_data': {
                    'total_population': cafe.rp_key.total_population,
                    'traffic_level': cafe.rp_key.traffic_level,
                }
            })
        
        # 통계 계산
        stats = {
            'total_cafes': queryset.count(),
            'total_businesses': sum(1 for cafe in queryset if cafe.biz_code),
            'risk_areas': len([cafe for cafe in queryset if self._get_cafe_status(cafe) == 'risk']),
            'avg_growth_rate': 7.9,  # 실제 계산 로직 필요
        }
        
        return Response({
            'map_data': map_data,
            'statistics': stats,
            'filters_applied': {
                'region': region,
                'major_category': major_category,
                'mid_category': mid_category,
                'franchise': franchise,
            }
        })
    
    def _get_cafe_status(self, cafe):
        """카페의 위험도 상태를 계산 (임시 로직)"""
        # 실제로는 매출, 리뷰, 트렌드 데이터를 기반으로 계산
        traffic_level = cafe.rp_key.traffic_level.lower()
        if '높음' in traffic_level:
            return 'safe'
        elif '보통' in traffic_level:
            return 'warning'
        else:
            return 'risk'

class CafeSalesViewSet(viewsets.ModelViewSet):
    queryset = CafeSales.objects.select_related("cafe").order_by("-date")
    serializer_class = CafeSalesSerializer
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['get'])
    def template_list(self, request):
        sales = self.get_queryset()
        context = {'sales': sales}
        return render(request, 'cafes/cafe_sales_list.html', context)

class CafeReviewViewSet(viewsets.ModelViewSet):
    queryset = CafeReview.objects.select_related("cafe").order_by("-review_id")
    serializer_class = CafeReviewSerializer
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['get'])
    def template_list(self, request):
        reviews = self.get_queryset()
        context = {'reviews': reviews}
        return render(request, 'cafes/cafe_review_list.html', context)

class CafeTrendAIViewSet(viewsets.ModelViewSet):
    queryset = CafeTrendAI.objects.select_related("rp_key").order_by("-trend_id")
    serializer_class = CafeTrendAISerializer
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['get'])
    def template_list(self, request):
        trends = self.get_queryset()
        context = {'trends': trends}
        return render(request, 'cafes/cafe_trend_list.html', context)


def pane_map_view(request):
    # URL 파라미터에서 필터 조건 가져오기
    region = request.GET.get('region', '서울시 전체')
    major_category = request.GET.get('major_category', 'type_all')
    mid_category = request.GET.get('mid_category', '전체')
    franchise = request.GET.get('franchise', '')
    
    # 기본 쿼리셋
    cafes = CafeId.objects.select_related("rp_key").all()
    
    # 지역 필터 적용
    if region and region != '서울시 전체':
        cafes = cafes.filter(address__icontains=region)
    
    # 업종 대분류 필터 적용
    if major_category and major_category != 'type_all':
        if major_category == 'franchise':
            cafes = cafes.filter(franchise=True)
        elif major_category == 'individual':
            cafes = cafes.filter(franchise=False)
    
    # 업종 중분류 필터 적용 (프랜차이즈 타입 기준)
    if mid_category and mid_category != '전체':
        cafes = cafes.filter(franchise_type__icontains=mid_category)
    
    # 특정 프랜차이즈 필터 적용
    if franchise:
        cafes = cafes.filter(name__icontains=franchise)
    
    # 통계 계산
    total_count = cafes.count()
    franchise_count = cafes.filter(franchise=True).count()
    individual_count = cafes.filter(franchise=False).count()
    
    context = {
        'cafes': cafes,
        'total_count': total_count,
        'franchise_count': franchise_count,
        'individual_count': individual_count,
        'selected_region': region,
        'selected_major_category': major_category,
        'selected_mid_category': mid_category,
        'selected_franchise': franchise,
    }
    
    return render(request, 'cafes/pane_map.html', context)

def pane_franchise_view(request):
    from django.db.models import Count, Q
    
    # URL 파라미터에서 필터 조건 가져오기
    region = request.GET.get('region', '서울시 전체')
    major_category = request.GET.get('major_category', 'type_all')
    mid_category = request.GET.get('mid_category', '전체')
    franchise = request.GET.get('franchise', '')
    
    # 기본 쿼리셋
    cafes = CafeId.objects.select_related("rp_key").all()
    
    # 지역 필터 적용
    if region and region != '서울시 전체':
        cafes = cafes.filter(address__icontains=region)
    
    # 업종 대분류 필터 적용
    if major_category and major_category != 'type_all':
        if major_category == 'franchise':
            cafes = cafes.filter(franchise=True)
        elif major_category == 'individual':
            cafes = cafes.filter(franchise=False)
    
    # 업종 중분류 필터 적용 (프랜차이즈 타입 기준)
    if mid_category and mid_category != '전체':
        cafes = cafes.filter(franchise_type__icontains=mid_category)
    
    # 특정 프랜차이즈 필터 적용
    if franchise:
        cafes = cafes.filter(name__icontains=franchise)
    
    # 프랜차이즈별 통계 계산
    franchise_stats_raw = cafes.filter(franchise=True).values('franchise_type').annotate(
        count=Count('cafe_id')
    ).order_by('-count')
    
    # 프랜차이즈별 매출 추정값 계산
    franchise_stats = []
    for stat in franchise_stats_raw:
        franchise_stats.append({
            'franchise_type': stat['franchise_type'],
            'count': stat['count'],
            'estimated_sales': stat['count'] * 850  # 만원 단위
        })
    
    # 전체 통계 계산
    total_count = cafes.count()
    franchise_count = cafes.filter(franchise=True).count()
    individual_count = cafes.filter(franchise=False).count()
    
    # 위험도 분석 (임시 로직)
    safe_franchises = 0
    warning_franchises = 0
    risk_franchises = 0
    
    for stat in franchise_stats:
        count = stat['count']
        if count >= 5:
            safe_franchises += 1
        elif count >= 2:
            warning_franchises += 1
        else:
            risk_franchises += 1
    
    # 매출 추정 (임시 데이터)
    total_sales = total_count * 850  # 만원 단위
    
    context = {
        'cafes': cafes,
        'total_count': total_count,
        'franchise_count': franchise_count,
        'individual_count': individual_count,
        'franchise_stats': franchise_stats,
        'total_sales': total_sales,
        'safe_franchises': safe_franchises,
        'warning_franchises': warning_franchises,
        'risk_franchises': risk_franchises,
        'selected_region': region,
        'selected_major_category': major_category,
        'selected_mid_category': mid_category,
        'selected_franchise': franchise,
    }
    
    return render(request, 'cafes/pane_franchise.html', context)

def pane_trend_view(request):
    from django.db.models import Count, Q, Avg
    
    # URL 파라미터에서 필터 조건 가져오기
    region = request.GET.get('region', '서울시 전체')
    major_category = request.GET.get('major_category', 'type_all')
    mid_category = request.GET.get('mid_category', '전체')
    franchise = request.GET.get('franchise', '')
    
    # 기본 쿼리셋 (카페 데이터)
    cafes = CafeId.objects.select_related("rp_key").all()
    
    # 지역 필터 적용
    if region and region != '서울시 전체':
        cafes = cafes.filter(address__icontains=region)
    
    # 업종 대분류 필터 적용
    if major_category and major_category != 'type_all':
        if major_category == 'franchise':
            cafes = cafes.filter(franchise=True)
        elif major_category == 'individual':
            cafes = cafes.filter(franchise=False)
    
    # 업종 중분류 필터 적용
    if mid_category and mid_category != '전체':
        cafes = cafes.filter(franchise_type__icontains=mid_category)
    
    # 특정 프랜차이즈 필터 적용
    if franchise:
        cafes = cafes.filter(name__icontains=franchise)
    
    # 필터링된 카페들의 rp_key를 기반으로 트렌드 데이터 가져오기
    rp_keys = cafes.values_list('rp_key', flat=True).distinct()
    trends = CafeTrendAI.objects.filter(rp_key__in=rp_keys)
    
    # 트렌드 통계 계산
    trend_stats = trends.aggregate(
        avg_growth_rate=Avg('predicted_growth_rate'),
        trendy_count=Count('trend_id', filter=Q(is_trendy=True)),
        growth_expectation_count=Count('trend_id', filter=Q(is_growth_expectation=True)),
        investment_opportunity_count=Count('trend_id', filter=Q(investment_opportunity=True)),
        risk_area_count=Count('trend_id', filter=Q(is_risk_area=True))
    )
    
    # 추천 레벨별 통계
    recommendation_stats = trends.values('recommendation_level').annotate(
        count=Count('trend_id')
    ).order_by('-recommendation_level')
    
    # 트렌드 카테고리별 분석 (임시 데이터 기반)
    trend_categories = []
    if trend_stats['trendy_count'] > 0:
        trend_categories.append({
            'name': '트렌디 지역',
            'growth_rate': 150,
            'count': trend_stats['trendy_count']
        })
    if trend_stats['growth_expectation_count'] > 0:
        trend_categories.append({
            'name': '성장 기대',
            'growth_rate': 120,
            'count': trend_stats['growth_expectation_count']
        })
    if trend_stats['investment_opportunity_count'] > 0:
        trend_categories.append({
            'name': '투자 기회',
            'growth_rate': 95,
            'count': trend_stats['investment_opportunity_count']
        })
    
    # 전체 통계 계산
    total_count = cafes.count()
    total_trends = trends.count()
    
    # 3년 성장률 (평균 예측 성장률 기반)
    three_year_growth = trend_stats['avg_growth_rate'] or 0
    
    # 신규 사업자 수 (성장 기대 지역 기반)
    new_businesses = trend_stats['growth_expectation_count'] or 0
    
    # 평균 생존율 (위험 지역이 아닌 곳의 비율)
    total_analyzed = total_trends if total_trends > 0 else 1
    survival_rate = ((total_trends - (trend_stats['risk_area_count'] or 0)) / total_analyzed) * 100
    
    # 월 평균 매출 지수 (추천 레벨 기반)
    avg_recommendation = trends.aggregate(avg_rec=Avg('recommendation_level'))['avg_rec'] or 3
    sales_index = int(avg_recommendation * 25)  # 1-5 레벨을 25-125 지수로 변환
    
    context = {
        'cafes': cafes,
        'trends': trends,
        'total_count': total_count,
        'total_trends': total_trends,
        'three_year_growth': round(three_year_growth, 1),
        'new_businesses': new_businesses,
        'survival_rate': round(survival_rate, 1),
        'sales_index': sales_index,
        'trend_categories': trend_categories,
        'trend_stats': trend_stats,
        'recommendation_stats': recommendation_stats,
        'selected_region': region,
        'selected_major_category': major_category,
        'selected_mid_category': mid_category,
        'selected_franchise': franchise,
    }
    
    return render(request, 'cafes/pane_trend.html', context)

def pane_report_view(request):
    return render(request, 'cafes/pane_report.html')
