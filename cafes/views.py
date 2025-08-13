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
        return render(request, 'cafes/cafe_list.html', context)
    
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
