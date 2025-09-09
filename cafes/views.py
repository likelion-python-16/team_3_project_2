from django.db.models import Avg, Count, Q
from django.shortcuts import render
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import CafeId, CafeTrendAI
from .serializers import (
    CafeIdSerializer,
)


class CafeIdViewSet(viewsets.ModelViewSet):
    queryset = CafeId.objects.select_related("rp_key").order_by("name")
    serializer_class = CafeIdSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=["get"])
    def template_list(self, request):

        from django.db.models import Avg

        cafes = self.get_queryset()

        # 지역 목록 (구 단위 중복 제거)
        distinct_list = (
            CafeId.objects.values_list("distinct", flat=True)
            .distinct()
            .order_by("distinct")
        )

        # 업종 중분류 목록 (franchise_type 중복 제거)
        franchise_type_list = (
            CafeId.objects.filter(franchise_type__isnull=False)
            .exclude(franchise_type="")
            .values_list("franchise_type", flat=True)
            .distinct()
            .order_by("franchise_type")
        )

        # 프랜차이즈가 True인 franchise_type을 중복 제거하고 4개만 가져오기
        franchise_types = (
            CafeId.objects.filter(franchise=True, franchise_type__isnull=False)
            .exclude(franchise_type="")
            .values_list("franchise_type", flat=True)
            .distinct()[:4]
        )

        # 주요 지표 계산
        # 1. 총 상가수 (전체 카페 수)
        total_stores = CafeId.objects.count()

        # 2. 매출 증가율 (트렌드 데이터 기반)
        trends = CafeTrendAI.objects.all()
        avg_growth_rate = (
            trends.aggregate(avg_growth=Avg("predicted_growth_rate"))["avg_growth"] or 0
        )
        growth_rate_formatted = (
            f"+{avg_growth_rate:.1f}%"
            if avg_growth_rate > 0
            else f"{avg_growth_rate:.1f}%"
        )

        # 3. 위험 지역 (is_risk_area가 True인 지역 수)
        risk_areas_count = trends.filter(is_risk_area=True).count()

        # 4. 신규 창업 (investment_opportunity가 True인 지역 수를 신규 창업 지표로 활용)
        new_businesses = trends.filter(investment_opportunity=True).count()

        context = {
            "cafes": cafes,
            "distinct_list": distinct_list,
            "franchise_type_list": franchise_type_list,
            "franchise_types": franchise_types,
            "total_stores": total_stores,
            "growth_rate": growth_rate_formatted,
            "risk_areas_count": risk_areas_count,
            "new_businesses": new_businesses,
        }
        return render(request, "index.html", context)

    @action(detail=False, methods=["get"])
    def map_markers(self, request):
        """지도 마커용 카페 데이터를 반환하는 API - 인증 불필요"""
        queryset = self.get_queryset()

        # 지역 필터
        region = request.query_params.get("region")
        if region and region != "서울시 전체":
            queryset = queryset.filter(distinct=region)

        # 업종 대분류 필터
        major_category = request.query_params.get("major_category")
        if major_category and major_category != "type_all":
            if major_category == "franchise":
                queryset = queryset.filter(franchise=True)
            elif major_category == "individual":
                queryset = queryset.filter(franchise=False)

        # 업종 중분류 필터
        mid_category = request.query_params.get("mid_category")
        if mid_category and mid_category != "전체":
            queryset = queryset.filter(franchise_type__icontains=mid_category)

        # 지도용 마커 데이터 포맷 (최소 정보만)
        markers_data = []
        for cafe in queryset:
            markers_data.append(
                {
                    "id": cafe.cafe_id,
                    "name": cafe.name,
                    "latitude": float(cafe.latitude),
                    "longitude": float(cafe.longitude),
                    "status": self._get_cafe_status(cafe),
                    "franchise": cafe.franchise,
                    "district": cafe.distinct,
                    "detail_address": cafe.detail_address,
                }
            )

        return Response(
            {"success": True, "markers": markers_data, "total_count": len(markers_data)}
        )

    @action(detail=False, methods=["get"])
    def filtered_data(self, request):
        """필터링된 카페 데이터를 반환하는 API - 인증 필요"""
        if not request.user.is_authenticated:
            return Response(
                {
                    "success": False,
                    "message": "로그인이 필요한 서비스입니다.",
                    "require_login": True,
                },
                status=401,
            )

        queryset = self.get_queryset()

        # 지역 필터 - 다른 뷰와 동일한 방식 사용
        region = request.query_params.get("region")
        if region and region != "서울시 전체":
            queryset = queryset.filter(distinct=region)

        # 업종 대분류 필터 - 다른 뷰와 동일한 방식 사용
        major_category = request.query_params.get("major_category")
        if major_category and major_category != "type_all":
            if major_category == "franchise":
                queryset = queryset.filter(franchise=True)
            elif major_category == "individual":
                queryset = queryset.filter(franchise=False)

        # 업종 중분류 필터 - 다른 뷰와 동일한 방식 사용
        mid_category = request.query_params.get("mid_category")
        if mid_category and mid_category != "전체":
            queryset = queryset.filter(franchise_type__icontains=mid_category)

        # 프랜차이즈 필터
        franchise = request.query_params.get("franchise")
        if franchise:
            queryset = queryset.filter(name__icontains=franchise)

        # 지도용 데이터 포맷
        map_data = []
        for cafe in queryset:
            map_data.append(
                {
                    "id": cafe.cafe_id,
                    "name": cafe.name,
                    "detail_address": cafe.detail_address,
                    "latitude": cafe.latitude,
                    "longitude": cafe.longitude,
                    "status": self._get_cafe_status(cafe),  # 안정/주의/위험 상태
                    "business_code": cafe.biz_code,
                    "population_data": {
                        "total_population": cafe.rp_key.total_population,
                        "traffic_level": cafe.rp_key.traffic_level,
                    },
                }
            )

        # 통계 계산
        stats = {
            "total_cafes": queryset.count(),
            "total_businesses": sum(1 for cafe in queryset if cafe.biz_code),
            "risk_areas": len(
                [cafe for cafe in queryset if self._get_cafe_status(cafe) == "risk"]
            ),
            "avg_growth_rate": 7.9,  # 실제 계산 로직 필요
        }

        return Response(
            {
                "map_data": map_data,
                "statistics": stats,
                "filters_applied": {
                    "region": region,
                    "major_category": major_category,
                    "mid_category": mid_category,
                    "franchise": franchise,
                },
            }
        )

    @action(detail=False, methods=["get"])
    def region_stats(self, request):
        """지역별 통계 데이터를 반환하는 API"""
        region = request.query_params.get("region", "서울시 전체")
        major_category = request.query_params.get("major_category", "type_all")
        mid_category = request.query_params.get("mid_category", "전체")

        # 기본 쿼리셋
        cafes = CafeId.objects.select_related("rp_key").all()

        # 지역 필터 적용
        if region and region != "서울시 전체":
            cafes = cafes.filter(distinct=region)

        # 업종 대분류 필터 적용
        if major_category and major_category != "type_all":
            if major_category == "franchise":
                cafes = cafes.filter(franchise=True)
            elif major_category == "individual":
                cafes = cafes.filter(franchise=False)

        # 업종 중분류 필터 적용
        if mid_category and mid_category != "전체":
            cafes = cafes.filter(franchise_type__icontains=mid_category)

        # 통계 계산
        total_stores = cafes.count()

        # 필터링된 카페들의 rp_key를 기반으로 트렌드 데이터 가져오기
        rp_keys = cafes.values_list("rp_key", flat=True).distinct()
        trends = CafeTrendAI.objects.filter(rp_key__in=rp_keys)

        # 평균 성장률 계산
        from django.db.models import Avg

        avg_growth_rate = (
            trends.aggregate(avg_growth=Avg("predicted_growth_rate"))["avg_growth"] or 0
        )
        growth_rate_formatted = (
            f"+{avg_growth_rate:.1f}%"
            if avg_growth_rate > 0
            else f"{avg_growth_rate:.1f}%"
        )

        # 위험지역 수 계산
        risk_areas_count = trends.filter(is_risk_area=True).count()

        # 신규 창업 (투자 기회 지역 수)
        new_businesses = trends.filter(investment_opportunity=True).count()

        return Response(
            {
                "total_stores": total_stores,
                "growth_rate": growth_rate_formatted,
                "risk_areas_count": risk_areas_count,
                "new_businesses": new_businesses,
                "region": region,
                "major_category": major_category,
                "mid_category": mid_category,
            }
        )

    def _get_cafe_status(self, cafe):
        """카페의 위험도 상태를 계산 (임시 로직)"""
        # 실제로는 매출, 리뷰, 트렌드 데이터를 기반으로 계산
        traffic_level = cafe.rp_key.traffic_level.lower()
        if "높음" in traffic_level:
            return "safe"
        elif "보통" in traffic_level:
            return "warning"
        else:
            return "risk"

    @action(detail=False, methods=["get"])
    def store_count_analysis(self, request):
        """상권 수 상세 분석 API"""
        # 필터 조건 가져오기
        region = request.query_params.get("region")
        major_category = request.query_params.get("major_category")
        mid_category = request.query_params.get("mid_category")

        # 기본 쿼리셋
        cafes = CafeId.objects.select_related("rp_key").all()

        # 지역 필터 적용
        if region and region != "서울시 전체":
            cafes = cafes.filter(distinct=region)

        # 업종 대분류 필터 적용
        if major_category and major_category != "type_all":
            if major_category == "franchise":
                cafes = cafes.filter(franchise=True)
            elif major_category == "individual":
                cafes = cafes.filter(franchise=False)

        # 업종 중분류 필터 적용
        if mid_category and mid_category != "전체":
            cafes = cafes.filter(franchise_type__icontains=mid_category)

        # 분석 데이터 계산

        total_count = cafes.count()
        franchise_count = cafes.filter(franchise=True).count()
        individual_count = cafes.filter(franchise=False).count()

        # 비율 계산
        franchise_ratio = (
            round((franchise_count / total_count) * 100, 1) if total_count > 0 else 0
        )
        individual_ratio = (
            round((individual_count / total_count) * 100, 1) if total_count > 0 else 0
        )

        # 프랜차이즈 타입별 분포
        franchise_distribution = (
            cafes.filter(franchise=True, franchise_type__isnull=False)
            .exclude(franchise_type="")
            .values("franchise_type")
            .annotate(count=Count("cafe_id"))
            .order_by("-count")[:10]
        )

        # 지역별 분포
        district_distribution = (
            cafes.values("distinct")
            .annotate(count=Count("cafe_id"))
            .order_by("-count")[:10]
        )

        return Response(
            {
                "total_count": total_count,
                "franchise_count": franchise_count,
                "individual_count": individual_count,
                "franchise_ratio": franchise_ratio,
                "individual_ratio": individual_ratio,
                "franchise_distribution": list(franchise_distribution),
                "district_distribution": [
                    {"district": item["distinct"], "count": item["count"]}
                    for item in district_distribution
                ],
            }
        )

    @action(detail=False, methods=["get"])
    def business_analysis(self, request):
        """사업자 상세 분석 API"""
        # 필터 조건 가져오기
        region = request.query_params.get("region")
        major_category = request.query_params.get("major_category")
        mid_category = request.query_params.get("mid_category")

        # 기본 쿼리셋
        cafes = CafeId.objects.select_related("rp_key").all()

        # 지역 필터 적용
        if region and region != "서울시 전체":
            cafes = cafes.filter(distinct=region)

        # 업종 대분류 필터 적용
        if major_category and major_category != "type_all":
            if major_category == "franchise":
                cafes = cafes.filter(franchise=True)
            elif major_category == "individual":
                cafes = cafes.filter(franchise=False)

        # 업종 중분류 필터 적용
        if mid_category and mid_category != "전체":
            cafes = cafes.filter(franchise_type__icontains=mid_category)

        # 분석 데이터 계산
        from datetime import datetime, timedelta

        total_businesses = cafes.count()

        # 매출 기반 분석 (CafeSales 모델 활용)
        # 최근 3개월 매출 데이터 기준
        current_date = datetime.now()
        recent_months = []
        for i in range(3):
            date = current_date - timedelta(days=30 * i)
            recent_months.append(f"{date.year:04d}-{date.month:02d}")

        # 매출 구간별 분포 (임시 계산)
        high_sales_count = int(total_businesses * 0.15)  # 상위 15%
        mid_sales_count = int(total_businesses * 0.35)  # 중간 35%
        low_sales_count = total_businesses - high_sales_count - mid_sales_count

        # 위험 사업자 수 (트렌드 데이터 기반)
        rp_keys = cafes.values_list("rp_key", flat=True).distinct()
        trends = CafeTrendAI.objects.filter(rp_key__in=rp_keys, is_risk_area=True)
        risk_business_count = trends.count()

        return Response(
            {
                "total_businesses": total_businesses,
                "avg_operation_period": 24,  # 평균 24개월 (임시 데이터)
                "new_businesses": int(total_businesses * 0.12),  # 신규 12% (임시)
                "high_sales_count": high_sales_count,
                "mid_sales_count": mid_sales_count,
                "low_sales_count": low_sales_count,
                "risk_business_count": risk_business_count,
            }
        )

    @action(detail=False, methods=["get"])
    def growth_rate_analysis(self, request):
        """성장률 상세 분석 API"""
        # 필터 조건 가져오기
        region = request.query_params.get("region")
        major_category = request.query_params.get("major_category")
        mid_category = request.query_params.get("mid_category")

        # 기본 쿼리셋
        cafes = CafeId.objects.select_related("rp_key").all()

        # 지역 필터 적용
        if region and region != "서울시 전체":
            cafes = cafes.filter(distinct=region)

        # 업종 대분류 필터 적용
        if major_category and major_category != "type_all":
            if major_category == "franchise":
                cafes = cafes.filter(franchise=True)
            elif major_category == "individual":
                cafes = cafes.filter(franchise=False)

        # 업종 중분류 필터 적용
        if mid_category and mid_category != "전체":
            cafes = cafes.filter(franchise_type__icontains=mid_category)

        # 트렌드 데이터 기반 성장률 분석
        from django.db.models import Avg

        rp_keys = cafes.values_list("rp_key", flat=True).distinct()
        trends = CafeTrendAI.objects.filter(rp_key__in=rp_keys)

        # 평균 성장률
        current_growth_rate = (
            trends.aggregate(avg_growth=Avg("predicted_growth_rate"))["avg_growth"] or 0
        )

        # 프랜차이즈별 성장률
        franchise_growth = []
        franchise_types = (
            cafes.filter(franchise=True, franchise_type__isnull=False)
            .exclude(franchise_type="")
            .values_list("franchise_type", flat=True)
            .distinct()
        )

        for franchise_type in franchise_types[:5]:  # 상위 5개
            franchise_cafes = cafes.filter(franchise_type=franchise_type)
            franchise_rp_keys = franchise_cafes.values_list(
                "rp_key", flat=True
            ).distinct()
            franchise_trends = CafeTrendAI.objects.filter(rp_key__in=franchise_rp_keys)

            avg_growth = (
                franchise_trends.aggregate(avg_growth=Avg("predicted_growth_rate"))[
                    "avg_growth"
                ]
                or 0
            )

            franchise_growth.append(
                {"franchise_type": franchise_type, "growth_rate": round(avg_growth, 1)}
            )

        return Response(
            {
                "current_growth_rate": round(current_growth_rate, 1),
                "yoy_change": round(current_growth_rate - 2.5, 1),  # 임시 계산
                "predicted_growth_rate": round(
                    current_growth_rate + 1.2, 1
                ),  # 임시 예측
                "franchise_growth": franchise_growth,
                "positive_factors": "지하철 2호선 연장, 대형 쇼핑몰 입점",
                "caution_factors": "임대료 상승세, 배달 서비스 확산",
                "negative_factors": "재택근무 증가, 인구 고령화",
            }
        )

    @action(detail=False, methods=["get"])
    def risk_area_analysis(self, request):
        """위험 지역 상세 분석 API"""
        # 필터 조건 가져오기
        region = request.query_params.get("region")
        major_category = request.query_params.get("major_category")
        mid_category = request.query_params.get("mid_category")

        # 기본 쿼리셋
        cafes = CafeId.objects.select_related("rp_key").all()

        # 지역 필터 적용
        if region and region != "서울시 전체":
            cafes = cafes.filter(distinct=region)

        # 업종 대분류 필터 적용
        if major_category and major_category != "type_all":
            if major_category == "franchise":
                cafes = cafes.filter(franchise=True)
            elif major_category == "individual":
                cafes = cafes.filter(franchise=False)

        # 업종 중분류 필터 적용
        if mid_category and mid_category != "전체":
            cafes = cafes.filter(franchise_type__icontains=mid_category)

        # 위험 지역 분석

        rp_keys = cafes.values_list("rp_key", flat=True).distinct()
        risk_trends = CafeTrendAI.objects.filter(rp_key__in=rp_keys, is_risk_area=True)

        total_risk_areas = risk_trends.count()

        # 위험도별 분류 (recommendation_level 기준)
        high_risk_areas = risk_trends.filter(recommendation_level__lte=2).count()
        medium_risk_areas = risk_trends.filter(recommendation_level=3).count()

        # 위험 지역 목록 (지역별)
        risk_area_list = []
        risk_districts = (
            cafes.filter(rp_key__in=risk_trends.values_list("rp_key", flat=True))
            .values("distinct")
            .annotate(count=Count("cafe_id"))
            .order_by("-count")[:10]
        )

        for district in risk_districts:
            district_cafes = cafes.filter(distinct=district["distinct"])
            district_rp_keys = district_cafes.values_list("rp_key", flat=True)
            district_risk_trends = CafeTrendAI.objects.filter(
                rp_key__in=district_rp_keys, is_risk_area=True
            )

            avg_recommendation = (
                district_risk_trends.aggregate(avg_rec=Avg("recommendation_level"))[
                    "avg_rec"
                ]
                or 5
            )

            risk_score = max(0, 100 - (avg_recommendation * 20))
            risk_level = (
                "high"
                if avg_recommendation <= 2
                else "medium"
                if avg_recommendation <= 3
                else "low"
            )

            risk_area_list.append(
                {
                    "area_name": district["distinct"],
                    "risk_score": int(risk_score),
                    "risk_level": risk_level,
                }
            )

        # 대안 지역 추천 (안전한 지역)
        safe_trends = CafeTrendAI.objects.filter(
            rp_key__in=rp_keys, is_risk_area=False, recommendation_level__gte=4
        )

        alternative_areas = []
        safe_districts = (
            cafes.filter(rp_key__in=safe_trends.values_list("rp_key", flat=True))
            .values("distinct")
            .annotate(count=Count("cafe_id"))
            .order_by("-count")[:5]
        )

        for district in safe_districts:
            district_cafes = cafes.filter(distinct=district["distinct"])
            district_rp_keys = district_cafes.values_list("rp_key", flat=True)
            district_safe_trends = CafeTrendAI.objects.filter(
                rp_key__in=district_rp_keys, is_risk_area=False
            )

            avg_recommendation = (
                district_safe_trends.aggregate(avg_rec=Avg("recommendation_level"))[
                    "avg_rec"
                ]
                or 3
            )

            safety_score = int(avg_recommendation * 20)

            alternative_areas.append(
                {"area_name": district["distinct"], "safety_score": safety_score}
            )

        return Response(
            {
                "total_risk_areas": total_risk_areas,
                "high_risk_areas": high_risk_areas,
                "medium_risk_areas": medium_risk_areas,
                "risk_area_list": risk_area_list,
                "alternative_areas": alternative_areas,
            }
        )

    @action(detail=False, methods=["get"])
    def franchise_cafe_count_analysis(self, request):
        """프랜차이즈 카페 수 상세 분석 API"""
        # 필터 조건 가져오기
        region = request.query_params.get("region")
        major_category = request.query_params.get("major_category")
        mid_category = request.query_params.get("mid_category")

        # 기본 쿼리셋
        cafes = CafeId.objects.select_related("rp_key").all()

        # 지역 필터 적용
        if region and region != "서울시 전체":
            cafes = cafes.filter(distinct=region)

        # 업종 대분류 필터 적용
        if major_category and major_category != "type_all":
            if major_category == "franchise":
                cafes = cafes.filter(franchise=True)
            elif major_category == "individual":
                cafes = cafes.filter(franchise=False)

        # 업종 중분류 필터 적용
        if mid_category and mid_category != "전체":
            cafes = cafes.filter(franchise_type__icontains=mid_category)

        # 분석 데이터 계산

        total_count = cafes.count()
        franchise_count = cafes.filter(franchise=True).count()
        individual_count = cafes.filter(franchise=False).count()

        # 비율 계산
        franchise_ratio = (
            round((franchise_count / total_count) * 100, 1) if total_count > 0 else 0
        )
        individual_ratio = (
            round((individual_count / total_count) * 100, 1) if total_count > 0 else 0
        )

        # 매장 규모별 분포 (임시 데이터)
        large_stores = int(total_count * 0.2)  # 20%
        medium_stores = int(total_count * 0.5)  # 50%
        small_stores = total_count - large_stores - medium_stores

        # 성장 추이 (트렌드 데이터 기반)
        rp_keys = cafes.values_list("rp_key", flat=True).distinct()
        trends = CafeTrendAI.objects.filter(rp_key__in=rp_keys)
        from django.db.models import Avg

        avg_growth = (
            trends.aggregate(avg_growth=Avg("predicted_growth_rate"))["avg_growth"] or 0
        )
        growth_trend = round(avg_growth * 3, 1)  # 3년 기준
        franchise_growth = round(avg_growth * 3.5, 1)  # 프랜차이즈가 더 높은 성장

        return Response(
            {
                "total_count": total_count,
                "franchise_count": franchise_count,
                "individual_count": individual_count,
                "franchise_ratio": franchise_ratio,
                "individual_ratio": individual_ratio,
                "large_stores": large_stores,
                "medium_stores": medium_stores,
                "small_stores": small_stores,
                "growth_trend": growth_trend,
                "franchise_growth": franchise_growth,
            }
        )

    @action(detail=False, methods=["get"])
    def franchise_type_analysis(self, request):
        """프랜차이즈 타입별 브랜드 분석 API"""
        # 필터 조건 가져오기
        region = request.query_params.get("region")
        major_category = request.query_params.get("major_category")
        mid_category = request.query_params.get("mid_category")

        # 기본 쿼리셋
        cafes = CafeId.objects.select_related("rp_key").all()

        # 지역 필터 적용
        if region and region != "서울시 전체":
            cafes = cafes.filter(distinct=region)

        # 업종 대분류 필터 적용
        if major_category and major_category != "type_all":
            if major_category == "franchise":
                cafes = cafes.filter(franchise=True)
            elif major_category == "individual":
                cafes = cafes.filter(franchise=False)

        # 업종 중분류 필터 적용
        if mid_category and mid_category != "전체":
            cafes = cafes.filter(franchise_type__icontains=mid_category)

        # 분석 데이터 계산

        franchise_count = cafes.filter(franchise=True).count()
        individual_count = cafes.filter(franchise=False).count()

        # 브랜드 다양성 계산
        brand_diversity = (
            cafes.filter(franchise=True, franchise_type__isnull=False)
            .exclude(franchise_type="")
            .values("franchise_type")
            .distinct()
            .count()
        )

        # 상위 프랜차이즈 브랜드
        top_franchises = (
            cafes.filter(franchise=True, franchise_type__isnull=False)
            .exclude(franchise_type="")
            .values("franchise_type")
            .annotate(count=Count("cafe_id"))
            .order_by("-count")[:10]
        )

        top_franchises_list = [
            {"brand_name": item["franchise_type"], "count": item["count"]}
            for item in top_franchises
        ]

        # 시장 점유율 계산
        total_count = cafes.count()
        franchise_market_share = (
            round((franchise_count / total_count) * 100, 1) if total_count > 0 else 0
        )
        individual_market_share = (
            round((individual_count / total_count) * 100, 1) if total_count > 0 else 0
        )

        return Response(
            {
                "franchise_count": franchise_count,
                "individual_count": individual_count,
                "brand_diversity": brand_diversity,
                "top_franchises": top_franchises_list,
                "franchise_market_share": franchise_market_share,
                "individual_market_share": individual_market_share,
            }
        )

    @action(detail=False, methods=["get"])
    def franchise_sales_analysis(self, request):
        """프랜차이즈 매출 분석 API"""
        # 필터 조건 가져오기
        region = request.query_params.get("region")
        major_category = request.query_params.get("major_category")
        mid_category = request.query_params.get("mid_category")

        # 기본 쿼리셋
        cafes = CafeId.objects.select_related("rp_key").all()

        # 지역 필터 적용
        if region and region != "서울시 전체":
            cafes = cafes.filter(distinct=region)

        # 업종 대분류 필터 적용
        if major_category and major_category != "type_all":
            if major_category == "franchise":
                cafes = cafes.filter(franchise=True)
            elif major_category == "individual":
                cafes = cafes.filter(franchise=False)

        # 업종 중분류 필터 적용
        if mid_category and mid_category != "전체":
            cafes = cafes.filter(franchise_type__icontains=mid_category)

        # 매출 분석 계산
        total_count = cafes.count()

        # 매출 추정 (매장당 평균 매출 850만원 기준)
        avg_sales_per_store = 850  # 만원
        total_sales = total_count * avg_sales_per_store
        avg_sales = avg_sales_per_store

        # 성장률 계산 (트렌드 데이터 기반)
        rp_keys = cafes.values_list("rp_key", flat=True).distinct()
        trends = CafeTrendAI.objects.filter(rp_key__in=rp_keys)
        from django.db.models import Avg

        avg_growth_rate = (
            trends.aggregate(avg_growth=Avg("predicted_growth_rate"))["avg_growth"] or 0
        )
        sales_growth = round(avg_growth_rate, 1)

        # 매출 구간별 분포 (임시 계산)
        high_sales_stores = int(total_count * 0.15)  # 상위 15%
        mid_sales_stores = int(total_count * 0.35)  # 중간 35%
        low_mid_sales_stores = int(total_count * 0.35)  # 중하위 35%
        low_sales_stores = (
            total_count - high_sales_stores - mid_sales_stores - low_mid_sales_stores
        )

        # 매출 요인 분석 (지역별 특성 고려)
        positive_factors = "유동인구 증가, 브랜드 인지도, 접근성 우수"
        caution_factors = "경쟁 심화, 임대료 상승"
        negative_factors = "시장 포화, 소비 패턴 변화"

        if region and region != "서울시 전체":
            if "강남" in region or "서초" in region:
                positive_factors = "높은 구매력, 프리미엄 시장, 유동인구"
            elif "구로" in region or "금천" in region:
                positive_factors = "직장인 밀집, 합리적 임대료, 교통 편리"

        return Response(
            {
                "total_sales": total_sales,
                "avg_sales": avg_sales,
                "sales_growth": sales_growth,
                "high_sales_stores": high_sales_stores,
                "mid_sales_stores": mid_sales_stores,
                "low_mid_sales_stores": low_mid_sales_stores,
                "low_sales_stores": low_sales_stores,
                "positive_factors": positive_factors,
                "caution_factors": caution_factors,
                "negative_factors": negative_factors,
            }
        )

    @action(detail=False, methods=["get"])
    def franchise_growth_analysis(self, request):
        """프랜차이즈 성장률 분석 API"""
        # 필터 조건 가져오기
        region = request.query_params.get("region")
        major_category = request.query_params.get("major_category")
        mid_category = request.query_params.get("mid_category")

        # 기본 쿼리셋
        cafes = CafeId.objects.select_related("rp_key").all()

        # 지역 필터 적용
        if region and region != "서울시 전체":
            cafes = cafes.filter(distinct=region)

        # 업종 대분류 필터 적용
        if major_category and major_category != "type_all":
            if major_category == "franchise":
                cafes = cafes.filter(franchise=True)
            elif major_category == "individual":
                cafes = cafes.filter(franchise=False)

        # 업종 중분류 필터 적용
        if mid_category and mid_category != "전체":
            cafes = cafes.filter(franchise_type__icontains=mid_category)

        # 성장률 분석
        from django.db.models import Avg

        rp_keys = cafes.values_list("rp_key", flat=True).distinct()
        trends = CafeTrendAI.objects.filter(rp_key__in=rp_keys)

        # 평균 성장률 계산
        avg_growth_rate = (
            trends.aggregate(avg_growth=Avg("predicted_growth_rate"))["avg_growth"] or 0
        )
        yoy_change = round(avg_growth_rate - 2.8, 1)  # 전년 대비 (임시 기준값 2.8%)
        predicted_growth = round(avg_growth_rate + 1.5, 1)  # 예상 성장률

        # 성장률 상위 브랜드
        growth_leaders = []
        franchise_types = (
            cafes.filter(franchise=True, franchise_type__isnull=False)
            .exclude(franchise_type="")
            .values_list("franchise_type", flat=True)
            .distinct()
        )

        for franchise_type in franchise_types[:8]:  # 상위 8개
            franchise_cafes = cafes.filter(franchise_type=franchise_type)
            franchise_rp_keys = franchise_cafes.values_list(
                "rp_key", flat=True
            ).distinct()
            franchise_trends = CafeTrendAI.objects.filter(rp_key__in=franchise_rp_keys)

            brand_growth = (
                franchise_trends.aggregate(avg_growth=Avg("predicted_growth_rate"))[
                    "avg_growth"
                ]
                or 0
            )

            growth_leaders.append(
                {"brand_name": franchise_type, "growth_rate": round(brand_growth, 1)}
            )

        # 성장률별 정렬
        growth_leaders = sorted(
            growth_leaders, key=lambda x: x["growth_rate"], reverse=True
        )

        # 시장 상황 분석
        market_condition = "안정적"
        if avg_growth_rate > 5:
            market_condition = "활발한 성장"
        elif avg_growth_rate < 0:
            market_condition = "침체"
        elif avg_growth_rate < 2:
            market_condition = "정체"

        # 성장 동력
        growth_drivers = "브랜드 확장, 메뉴 다양화, 디지털 마케팅 강화"
        if region and region != "서울시 전체":
            if "강남" in region or "서초" in region:
                growth_drivers = "프리미엄 브랜드 확산, 고급화 전략, 체험형 매장"
            elif "성동" in region or "광진" in region:
                growth_drivers = "젊은층 타겟, SNS 마케팅, 독특한 컨셉"

        return Response(
            {
                "avg_growth_rate": round(avg_growth_rate, 1),
                "yoy_change": yoy_change,
                "predicted_growth": predicted_growth,
                "growth_leaders": growth_leaders,
                "market_condition": market_condition,
                "growth_drivers": growth_drivers,
            }
        )

    @action(detail=False, methods=["get"])
    def trend_three_year_growth_analysis(self, request):
        """3년 성장률 트렌드 분석 API"""
        # 필터 조건 가져오기
        region = request.query_params.get("region")
        major_category = request.query_params.get("major_category")
        mid_category = request.query_params.get("mid_category")

        # 기본 쿼리셋
        cafes = CafeId.objects.select_related("rp_key").all()

        # 지역 필터 적용
        if region and region != "서울시 전체":
            cafes = cafes.filter(distinct=region)

        # 업종 대분류 필터 적용
        if major_category and major_category != "type_all":
            if major_category == "franchise":
                cafes = cafes.filter(franchise=True)
            elif major_category == "individual":
                cafes = cafes.filter(franchise=False)

        # 업종 중분류 필터 적용
        if mid_category and mid_category != "전체":
            cafes = cafes.filter(franchise_type__icontains=mid_category)

        # 3년 성장률 분석
        from datetime import datetime

        from django.db.models import Avg

        rp_keys = cafes.values_list("rp_key", flat=True).distinct()
        trends = CafeTrendAI.objects.filter(rp_key__in=rp_keys)

        # 3년 평균 성장률 계산
        avg_growth_rate = (
            trends.aggregate(avg_growth=Avg("predicted_growth_rate"))["avg_growth"] or 0
        )
        three_year_growth = round(avg_growth_rate * 3, 1)  # 3년 누적 성장률
        annual_avg_growth = round(avg_growth_rate, 1)

        # 최고 성장 연도 계산 (임시)
        current_year = datetime.now().year
        peak_growth_year = current_year - 1  # 작년이 최고 성장률

        # 연도별 성장률 (임시 데이터)
        yearly_growth = []
        for i in range(3):
            year = current_year - i
            # 실제로는 각 연도별 데이터를 계산해야 하지만, 임시로 변동값 적용
            growth_rate = round(avg_growth_rate + (i * 0.5) - 1, 1)
            yearly_growth.append({"year": str(year), "growth_rate": growth_rate})

        yearly_growth.reverse()  # 시간순 정렬

        # 성장 동력 및 전망
        growth_drivers = "배달 서비스 확산, 원두 품질 향상, 공간 다양화"
        caution_factors = "임대료 상승, 인건비 증가"
        future_outlook = "안정적 성장세 지속 예상"

        if region and region != "서울시 전체":
            if "강남" in region or "서초" in region:
                growth_drivers = (
                    "프리미엄 시장 확산, 오피스 카페 증가, 고급 브랜드 확장"
                )
                future_outlook = "지속적인 고급화로 성장 가능성 높음"

        return Response(
            {
                "three_year_growth": three_year_growth,
                "annual_avg_growth": annual_avg_growth,
                "peak_growth_year": peak_growth_year,
                "yearly_growth": yearly_growth,
                "growth_drivers": growth_drivers,
                "caution_factors": caution_factors,
                "future_outlook": future_outlook,
            }
        )

    @action(detail=False, methods=["get"])
    def trend_new_business_analysis(self, request):
        """신규 사업자 현황 분석 API"""
        # 필터 조건 가져오기
        region = request.query_params.get("region")
        major_category = request.query_params.get("major_category")
        mid_category = request.query_params.get("mid_category")

        # 기본 쿼리셋
        cafes = CafeId.objects.select_related("rp_key").all()

        # 지역 필터 적용
        if region and region != "서울시 전체":
            cafes = cafes.filter(distinct=region)

        # 업종 대분류 필터 적용
        if major_category and major_category != "type_all":
            if major_category == "franchise":
                cafes = cafes.filter(franchise=True)
            elif major_category == "individual":
                cafes = cafes.filter(franchise=False)

        # 업종 중분류 필터 적용
        if mid_category and mid_category != "전체":
            cafes = cafes.filter(franchise_type__icontains=mid_category)

        # 신규 사업자 분석
        from django.db.models import Avg

        total_count = cafes.count()
        rp_keys = cafes.values_list("rp_key", flat=True).distinct()
        trends = CafeTrendAI.objects.filter(rp_key__in=rp_keys)

        # 투자 기회 지역을 신규 사업자로 간주
        new_businesses = max(1, int(total_count * 0.08))  # 전체의 8% 정도를 신규로 가정

        # 전년 동기 대비 계산 (임시)
        avg_growth = (
            trends.aggregate(avg_growth=Avg("predicted_growth_rate"))["avg_growth"] or 0
        )
        yoy_change = round(avg_growth * 1.2, 1)  # 신규 사업자는 성장률보다 높은 변동성

        # 성공률 계산 (위험 지역이 아닌 곳의 비율)
        total_trends = trends.count()
        risk_areas = trends.filter(is_risk_area=True).count()
        success_rate = round(
            ((total_trends - risk_areas) / max(1, total_trends)) * 100, 1
        )

        # 신규 사업자 유형별 분포
        franchise_count = cafes.filter(franchise=True).count()
        individual_count = cafes.filter(franchise=False).count()

        new_franchise = int(new_businesses * (franchise_count / max(1, total_count)))
        new_individual = int(new_businesses * (individual_count / max(1, total_count)))
        new_hybrid = new_businesses - new_franchise - new_individual

        # 선호 지역 (투자 기회가 많은 지역)
        preferred_areas = []
        safe_areas = (
            cafes.filter(
                rp_key__in=trends.filter(
                    investment_opportunity=True, is_risk_area=False
                ).values_list("rp_key", flat=True)
            )
            .values("distinct")
            .annotate(count=Count("cafe_id"))
            .order_by("-count")[:5]
        )

        for area in safe_areas:
            preferred_areas.append(
                {
                    "area_name": area["distinct"],
                    "new_count": max(
                        1, int(area["count"] * 0.1)
                    ),  # 해당 지역 카페의 10%
                }
            )

        # 성공 요인
        success_factors = "차별화된 컨셉, 좋은 입지, 품질 관리"
        key_success_factor = "고객 서비스"

        if region and region != "서울시 전체":
            if "성동" in region or "광진" in region:
                success_factors = "SNS 마케팅, 젊은층 타겟, 독특한 인테리어"
                key_success_factor = "트렌드 대응"
            elif "강남" in region or "서초" in region:
                success_factors = "프리미엄 품질, 브랜드 신뢰도, 서비스 차별화"
                key_success_factor = "품질 우수성"

        return Response(
            {
                "new_businesses": new_businesses,
                "yoy_change": yoy_change,
                "success_rate": success_rate,
                "new_franchise": new_franchise,
                "new_individual": new_individual,
                "new_hybrid": max(0, new_hybrid),
                "preferred_areas": preferred_areas,
                "success_factors": success_factors,
                "key_success_factor": key_success_factor,
            }
        )

    @action(detail=False, methods=["get"])
    def trend_survival_rate_analysis(self, request):
        """카페 생존율 분석 API"""
        # 필터 조건 가져오기
        region = request.query_params.get("region")
        major_category = request.query_params.get("major_category")
        mid_category = request.query_params.get("mid_category")

        # 기본 쿼리셋
        cafes = CafeId.objects.select_related("rp_key").all()

        # 지역 필터 적용
        if region and region != "서울시 전체":
            cafes = cafes.filter(distinct=region)

        # 업종 대분류 필터 적용
        if major_category and major_category != "type_all":
            if major_category == "franchise":
                cafes = cafes.filter(franchise=True)
            elif major_category == "individual":
                cafes = cafes.filter(franchise=False)

        # 업종 중분류 필터 적용
        if mid_category and mid_category != "전체":
            cafes = cafes.filter(franchise_type__icontains=mid_category)

        # 생존율 분석

        rp_keys = cafes.values_list("rp_key", flat=True).distinct()
        trends = CafeTrendAI.objects.filter(rp_key__in=rp_keys)

        total_trends = trends.count()
        if total_trends == 0:
            total_trends = 1  # 0으로 나누기 방지

        # 기본 생존율 (위험 지역이 아닌 곳의 비율)
        safe_areas = trends.filter(is_risk_area=False).count()
        survival_rate = round((safe_areas / total_trends) * 100, 1)

        # 3년, 5년 생존율 (추천 레벨 기반으로 계산)
        high_recommendation = trends.filter(recommendation_level__gte=4).count()
        medium_recommendation = trends.filter(recommendation_level=3).count()

        three_year_survival = round((high_recommendation / total_trends) * 100, 1)
        five_year_survival = round(
            ((high_recommendation + medium_recommendation * 0.7) / total_trends) * 100,
            1,
        )

        # 유형별 생존율

        # 프랜차이즈 생존율 (일반적으로 더 높음)
        franchise_survival = min(100, round(survival_rate * 1.15, 1))
        individual_survival = max(0, round(survival_rate * 0.85, 1))
        small_franchise_survival = round(survival_rate * 1.05, 1)

        # 폐업 위험 요인 (위험 지역 특성 분석)
        risk_areas = trends.filter(is_risk_area=True).count()
        low_recommendation = trends.filter(recommendation_level__lte=2).count()

        low_sales_risk = round((risk_areas / total_trends) * 100, 1)
        high_rent_risk = round(
            (low_recommendation / total_trends) * 80, 1
        )  # 임대료는 추천도와 상관
        competition_risk = round(min(50, low_sales_risk * 0.8), 1)

        # 생존율 향상 방안
        survival_strategies = "꾸준한 품질 관리, 고객 관계 관리, 적절한 마케팅"
        key_survival_factor = "지속적인 메뉴 개발"

        if region and region != "서울시 전체":
            if "강남" in region or "서초" in region:
                survival_strategies = "프리미엄 서비스 유지, 브랜드 차별화, 고객 충성도"
                key_survival_factor = "서비스 품질"
            elif "구로" in region or "금천" in region:
                survival_strategies = "합리적 가격, 직장인 맞춤 서비스, 효율적 운영"
                key_survival_factor = "운영 효율성"

        return Response(
            {
                "survival_rate": survival_rate,
                "three_year_survival": three_year_survival,
                "five_year_survival": five_year_survival,
                "franchise_survival": franchise_survival,
                "individual_survival": individual_survival,
                "small_franchise_survival": small_franchise_survival,
                "low_sales_risk": low_sales_risk,
                "high_rent_risk": high_rent_risk,
                "competition_risk": competition_risk,
                "survival_strategies": survival_strategies,
                "key_survival_factor": key_survival_factor,
            }
        )

    @action(detail=False, methods=["get"])
    def trend_sales_index_analysis(self, request):
        """매출 지수 분석 API"""
        # 필터 조건 가져오기
        region = request.query_params.get("region")
        major_category = request.query_params.get("major_category")
        mid_category = request.query_params.get("mid_category")

        # 기본 쿼리셋
        cafes = CafeId.objects.select_related("rp_key").all()

        # 지역 필터 적용
        if region and region != "서울시 전체":
            cafes = cafes.filter(distinct=region)

        # 업종 대분류 필터 적용
        if major_category and major_category != "type_all":
            if major_category == "franchise":
                cafes = cafes.filter(franchise=True)
            elif major_category == "individual":
                cafes = cafes.filter(franchise=False)

        # 업종 중분류 필터 적용
        if mid_category and mid_category != "전체":
            cafes = cafes.filter(franchise_type__icontains=mid_category)

        # 매출 지수 분석

        from django.db.models import Avg

        rp_keys = cafes.values_list("rp_key", flat=True).distinct()
        trends = CafeTrendAI.objects.filter(rp_key__in=rp_keys)

        # 추천 레벨 기반 매출 지수 계산 (1-5 레벨을 20-120 지수로 변환)
        avg_recommendation = (
            trends.aggregate(avg_rec=Avg("recommendation_level"))["avg_rec"] or 3
        )
        sales_index = int(
            avg_recommendation * 24
        )  # 3레벨 = 72, 4레벨 = 96, 5레벨 = 120

        # 성장률 기반 변화율 계산
        avg_growth_rate = (
            trends.aggregate(avg_growth=Avg("predicted_growth_rate"))["avg_growth"] or 0
        )
        monthly_change = round(avg_growth_rate / 12, 1)  # 월별 변화율
        yearly_change = round(avg_growth_rate, 1)

        # 월별 매출 지수 추이 (임시 데이터)
        monthly_index = []
        base_index = sales_index
        for i in range(12):
            month = i + 1
            # 계절성 반영 (여름, 겨울에 높음)
            seasonal_factor = 1.0
            if month in [6, 7, 8, 12, 1, 2]:  # 여름, 겨울
                seasonal_factor = 1.1
            elif month in [3, 4, 5, 9, 10, 11]:  # 봄, 가을
                seasonal_factor = 0.95

            monthly_idx = int(base_index * seasonal_factor + (monthly_change * (i - 6)))
            monthly_index.append(
                {
                    "month": str(month),
                    "index": max(50, min(150, monthly_idx)),  # 50-150 범위로 제한
                }
            )

        # 지역별 매출 지수 (같은 지역 내에서도 구별 비교)
        regional_index = []
        if region and region != "서울시 전체":
            # 선택된 지역의 지수
            regional_index.append({"region": region, "index": sales_index})

            # 비교 지역들 (임시)
            comparison_regions = ["강남구", "서초구", "마포구", "성동구"]
            for comp_region in comparison_regions[:3]:
                if comp_region != region:
                    # 지역별 특성 반영한 지수
                    if "강남" in comp_region or "서초" in comp_region:
                        comp_index = int(sales_index * 1.2)  # 강남권 더 높음
                    else:
                        comp_index = int(sales_index * 0.9)  # 기타 지역

                    regional_index.append(
                        {"region": comp_region, "index": max(50, min(150, comp_index))}
                    )
        else:
            # 서울시 전체 선택시 구별 비교
            districts = ["강남구", "서초구", "마포구", "성동구", "구로구"]
            for district in districts:
                if "강남" in district or "서초" in district:
                    dist_index = int(sales_index * 1.15)
                elif "마포" in district or "성동" in district:
                    dist_index = int(sales_index * 1.05)
                else:
                    dist_index = int(sales_index * 0.9)

                regional_index.append(
                    {"region": district, "index": max(50, min(150, dist_index))}
                )

        # 매출 지수 영향 요인
        positive_factors = "소비 심리 회복, 외식 문화 확산, 프리미엄 커피 선호"
        neutral_factors = "계절적 변동, 경쟁 증가"
        negative_factors = "원자재 가격 상승, 인건비 증가"

        if region and region != "서울시 전체":
            if "강남" in region or "서초" in region:
                positive_factors = "높은 구매력, 프리미엄 시장, 오피스 수요"
                negative_factors = "높은 임대료, 치열한 경쟁"
            elif "구로" in region or "금천" in region:
                positive_factors = "직장인 수요, 합리적 가격대, 접근성"
                negative_factors = "제한적 구매력, 가격 경쟁 심화"

        return Response(
            {
                "sales_index": sales_index,
                "monthly_change": monthly_change,
                "yearly_change": yearly_change,
                "monthly_index": monthly_index,
                "regional_index": regional_index,
                "positive_factors": positive_factors,
                "neutral_factors": neutral_factors,
                "negative_factors": negative_factors,
            }
        )


def pane_map_view(request):
    from django.db.models import Avg

    # URL 파라미터에서 필터 조건 가져오기
    region = request.GET.get("region", "서울시 전체")
    major_category = request.GET.get("major_category", "type_all")
    mid_category = request.GET.get("mid_category", "전체")
    franchise = request.GET.get("franchise", "")

    # 기본 쿼리셋
    cafes = CafeId.objects.select_related("rp_key").all()

    # 지역 필터 적용 - region_stats API와 동일한 방식 사용
    if region and region != "서울시 전체":
        cafes = cafes.filter(distinct=region)

    # 업종 대분류 필터 적용
    if major_category and major_category != "type_all":
        if major_category == "franchise":
            cafes = cafes.filter(franchise=True)
        elif major_category == "individual":
            cafes = cafes.filter(franchise=False)

    # 업종 중분류 필터 적용 (프랜차이즈 타입 기준)
    if mid_category and mid_category != "전체":
        cafes = cafes.filter(franchise_type__icontains=mid_category)

    # 특정 프랜차이즈 필터 적용
    if franchise:
        cafes = cafes.filter(name__icontains=franchise)

    # 지역만 필터링된 전체 사업자 수 계산
    region_only_cafes = CafeId.objects.select_related("rp_key").all()
    if region and region != "서울시 전체":
        region_only_cafes = region_only_cafes.filter(distinct=region)
    total_businesses_by_region = region_only_cafes.count()

    # 통계 계산
    total_count = cafes.count()
    franchise_count = cafes.filter(franchise=True).count()
    individual_count = cafes.filter(franchise=False).count()

    # CafeTrendAI 모델에서 평균 성장률과 위험지역 수 계산
    # 필터링된 카페들의 rp_key를 기반으로 트렌드 데이터 가져오기
    rp_keys = cafes.values_list("rp_key", flat=True).distinct()
    trends = CafeTrendAI.objects.filter(rp_key__in=rp_keys)

    # 평균 성장률 계산
    avg_growth_rate = (
        trends.aggregate(avg_growth=Avg("predicted_growth_rate"))["avg_growth"] or 0
    )
    growth_rate_formatted = (
        f"+{avg_growth_rate:.1f}%" if avg_growth_rate > 0 else f"{avg_growth_rate:.1f}%"
    )

    # 위험지역 수 계산
    risk_areas_count = trends.filter(is_risk_area=True).count()

    context = {
        "cafes": cafes,
        "total_count": total_count,
        "total_businesses_by_region": total_businesses_by_region,
        "franchise_count": franchise_count,
        "individual_count": individual_count,
        "avg_growth_rate": growth_rate_formatted,
        "risk_areas_count": risk_areas_count,
        "selected_region": region,
        "selected_major_category": major_category,
        "selected_mid_category": mid_category,
        "selected_franchise": franchise,
    }

    return render(request, "cafes/pane_map.html", context)


def pane_franchise_view(request):
    from django.db.models import Avg

    # URL 파라미터에서 필터 조건 가져오기
    region = request.GET.get("region", "서울시 전체")
    major_category = request.GET.get("major_category", "type_all")
    mid_category = request.GET.get("mid_category", "전체")
    franchise = request.GET.get("franchise", "")

    # 기본 쿼리셋
    cafes = CafeId.objects.select_related("rp_key").all()

    # 지역 필터 적용 - region_stats API와 동일한 방식 사용
    if region and region != "서울시 전체":
        cafes = cafes.filter(distinct=region)

    # 업종 대분류 필터 적용
    if major_category and major_category != "type_all":
        if major_category == "franchise":
            cafes = cafes.filter(franchise=True)
        elif major_category == "individual":
            cafes = cafes.filter(franchise=False)

    # 업종 중분류 필터 적용 (프랜차이즈 타입 기준)
    if mid_category and mid_category != "전체":
        cafes = cafes.filter(franchise_type__icontains=mid_category)

    # 특정 프랜차이즈 필터 적용
    if franchise:
        cafes = cafes.filter(name__icontains=franchise)

    # 프랜차이즈별 통계 계산
    franchise_stats_raw = (
        cafes.filter(franchise=True)
        .values("franchise_type")
        .annotate(count=Count("cafe_id"))
        .order_by("-count")
    )

    # 프랜차이즈별 매출 추정값 계산
    franchise_stats = []
    for stat in franchise_stats_raw:
        franchise_stats.append(
            {
                "franchise_type": stat["franchise_type"],
                "count": stat["count"],
                "estimated_sales": stat["count"] * 850,  # 만원 단위
            }
        )

    # 전체 통계 계산
    total_count = cafes.count()
    franchise_count = cafes.filter(franchise=True).count()
    individual_count = cafes.filter(franchise=False).count()

    # CafeTrendAI 모델에서 평균 성장률 계산
    # 필터링된 카페들의 rp_key를 기반으로 트렌드 데이터 가져오기
    rp_keys = cafes.values_list("rp_key", flat=True).distinct()
    trends = CafeTrendAI.objects.filter(rp_key__in=rp_keys)

    # 평균 성장률 계산
    avg_growth_rate = (
        trends.aggregate(avg_growth=Avg("predicted_growth_rate"))["avg_growth"] or 0
    )
    growth_rate_formatted = (
        f"+{avg_growth_rate:.1f}%" if avg_growth_rate > 0 else f"{avg_growth_rate:.1f}%"
    )

    # 위험도 분석 (임시 로직)
    safe_franchises = 0
    warning_franchises = 0
    risk_franchises = 0

    for stat in franchise_stats:
        count = stat["count"]
        if count >= 5:
            safe_franchises += 1
        elif count >= 2:
            warning_franchises += 1
        else:
            risk_franchises += 1

    # 매출 추정 (임시 데이터)
    total_sales = total_count * 850  # 만원 단위

    context = {
        "cafes": cafes,
        "total_count": total_count,
        "franchise_count": franchise_count,
        "individual_count": individual_count,
        "franchise_stats": franchise_stats,
        "total_sales": total_sales,
        "avg_growth_rate": growth_rate_formatted,
        "safe_franchises": safe_franchises,
        "warning_franchises": warning_franchises,
        "risk_franchises": risk_franchises,
        "selected_region": region,
        "selected_major_category": major_category,
        "selected_mid_category": mid_category,
        "selected_franchise": franchise,
    }

    return render(request, "cafes/pane_franchise.html", context)


def pane_trend_view(request):
    from django.db.models import Avg

    # URL 파라미터에서 필터 조건 가져오기
    region = request.GET.get("region", "서울시 전체")
    major_category = request.GET.get("major_category", "type_all")
    mid_category = request.GET.get("mid_category", "전체")
    franchise = request.GET.get("franchise", "")

    # 기본 쿼리셋 (카페 데이터)
    cafes = CafeId.objects.select_related("rp_key").all()

    # 지역 필터 적용 - region_stats API와 동일한 방식 사용
    if region and region != "서울시 전체":
        cafes = cafes.filter(distinct=region)

    # 업종 대분류 필터 적용
    if major_category and major_category != "type_all":
        if major_category == "franchise":
            cafes = cafes.filter(franchise=True)
        elif major_category == "individual":
            cafes = cafes.filter(franchise=False)

    # 업종 중분류 필터 적용
    if mid_category and mid_category != "전체":
        cafes = cafes.filter(franchise_type__icontains=mid_category)

    # 특정 프랜차이즈 필터 적용
    if franchise:
        cafes = cafes.filter(name__icontains=franchise)

    # 필터링된 카페들의 rp_key를 기반으로 트렌드 데이터 가져오기
    rp_keys = cafes.values_list("rp_key", flat=True).distinct()
    trends = CafeTrendAI.objects.filter(rp_key__in=rp_keys)

    # 트렌드 통계 계산
    trend_stats = trends.aggregate(
        avg_growth_rate=Avg("predicted_growth_rate"),
        trendy_count=Count("trend_id", filter=Q(is_trendy=True)),
        growth_expectation_count=Count(
            "trend_id", filter=Q(is_growth_expectation=True)
        ),
        investment_opportunity_count=Count(
            "trend_id", filter=Q(investment_opportunity=True)
        ),
        risk_area_count=Count("trend_id", filter=Q(is_risk_area=True)),
    )

    # 추천 레벨별 통계
    recommendation_stats = (
        trends.values("recommendation_level")
        .annotate(count=Count("trend_id"))
        .order_by("-recommendation_level")
    )

    # 트렌드 카테고리별 분석 (임시 데이터 기반)
    trend_categories = []
    if trend_stats["trendy_count"] > 0:
        trend_categories.append(
            {
                "name": "트렌디 지역",
                "growth_rate": 150,
                "count": trend_stats["trendy_count"],
            }
        )
    if trend_stats["growth_expectation_count"] > 0:
        trend_categories.append(
            {
                "name": "성장 기대",
                "growth_rate": 120,
                "count": trend_stats["growth_expectation_count"],
            }
        )
    if trend_stats["investment_opportunity_count"] > 0:
        trend_categories.append(
            {
                "name": "투자 기회",
                "growth_rate": 95,
                "count": trend_stats["investment_opportunity_count"],
            }
        )

    # 전체 통계 계산
    total_count = cafes.count()
    total_trends = trends.count()

    # 3년 성장률 (평균 예측 성장률 기반)
    three_year_growth = trend_stats["avg_growth_rate"] or 0

    # 신규 사업자 수 (성장 기대 지역 기반)
    new_businesses = trend_stats["growth_expectation_count"] or 0

    # 평균 생존율 (위험 지역이 아닌 곳의 비율)
    total_analyzed = total_trends if total_trends > 0 else 1
    survival_rate = (
        (total_trends - (trend_stats["risk_area_count"] or 0)) / total_analyzed
    ) * 100

    # 월 평균 매출 지수 (추천 레벨 기반)
    avg_recommendation = (
        trends.aggregate(avg_rec=Avg("recommendation_level"))["avg_rec"] or 3
    )
    sales_index = int(avg_recommendation * 25)  # 1-5 레벨을 25-125 지수로 변환

    context = {
        "cafes": cafes,
        "trends": trends,
        "total_count": total_count,
        "total_trends": total_trends,
        "three_year_growth": round(three_year_growth, 1),
        "new_businesses": new_businesses,
        "survival_rate": round(survival_rate, 1),
        "sales_index": sales_index,
        "trend_categories": trend_categories,
        "trend_stats": trend_stats,
        "recommendation_stats": recommendation_stats,
        "selected_region": region,
        "selected_major_category": major_category,
        "selected_mid_category": mid_category,
        "selected_franchise": franchise,
    }

    return render(request, "cafes/pane_trend.html", context)


def pane_report_view(request):
    return render(request, "cafes/pane_report.html")
