from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import ResidentPopulation, CafeId, CafeSales

class CafeModelsTest(TestCase):
    def setUp(self):
        self.rp = ResidentPopulation.objects.create(
            total_population=10000,
            population_per_ages=2000,
            income_avg=5000,
            rent_avg=100,
            traffic_level='High'
        )
        self.cafe = CafeId.objects.create(
            name='Test Cafe',
            distinct='강남구',
            detail_address='테헤란로 123',
            latitude=37.5, 
            longitude=127.5,
            rp_key=self.rp
        )

    def test_cafe_id_creation(self):
        """CafeId 모델 객체 생성 테스트"""
        self.assertEqual(self.cafe.name, 'Test Cafe')
        self.assertEqual(self.cafe.city, '서울특별시')
        self.assertEqual(self.cafe.rp_key.total_population, 10000)

    def test_cafe_sales_creation(self):
        """CafeSales 모델 객체 생성 및 aov 속성 테스트"""
        sales = CafeSales.objects.create(
            cafe=self.cafe,
            date='2024-01',
            price=5000,
            visitor_count=100,
            sales=500000
        )
        self.assertEqual(sales.cafe.name, 'Test Cafe')
        self.assertEqual(sales.sales, 500000)
        self.assertEqual(sales.aov, 5000) # 500000 / 100

    def test_cafe_sales_aov_with_zero_visitors(self):
        """방문자 수가 0일 때 aov가 0을 반환하는지 테스트"""
        sales = CafeSales.objects.create(
            cafe=self.cafe,
            date='2024-02',
            price=5000,
            visitor_count=0,
            sales=0
        )
        self.assertEqual(sales.aov, 0)

    def test_cafe_sales_date_validation(self):
        """CafeSales의 date 필드 유효성 검사 테스트"""
        # 잘못된 형식
        with self.assertRaises(ValidationError):
            sales = CafeSales(cafe=self.cafe, date='2024/01', sales=1000, visitor_count=10, price=100)
            sales.full_clean()

        # 2000년 이전
        with self.assertRaises(ValidationError):
            sales = CafeSales(cafe=self.cafe, date='1999-12', sales=1000, visitor_count=10, price=100)
            sales.full_clean()
        
        # 현재 기준 다음달 데이터 (미래)
        next_month = timezone.now().replace(day=1) + timezone.timedelta(days=32)
        future_date_str = next_month.strftime('%Y-%m')
        with self.assertRaises(ValidationError):
            sales = CafeSales(cafe=self.cafe, date=future_date_str, sales=1000, visitor_count=10, price=100)
            sales.full_clean()

        # 유효한 형식 (지난달)
        last_month = timezone.now().replace(day=1) - timezone.timedelta(days=1)
        valid_date_str = last_month.strftime('%Y-%m')
        sales = CafeSales(cafe=self.cafe, date=valid_date_str, sales=1000, visitor_count=10, price=100)
        try:
            sales.full_clean() # Should not raise ValidationError
        except ValidationError:
            self.fail("Valid date raised ValidationError unexpectedly!")

    def test_unique_cafe_date_constraint(self):
        """동일한 카페에 동일한 날짜의 매출 데이터가 중복 저장되지 않는지 테스트"""
        CafeSales.objects.create(
            cafe=self.cafe,
            date='2024-03',
            price=5000,
            visitor_count=100,
            sales=500000
        )
        with self.assertRaises(Exception): # IntegrityError is expected
            CafeSales.objects.create(
                cafe=self.cafe,
                date='2024-03',
                price=6000,
                visitor_count=120,
                sales=720000
            )
