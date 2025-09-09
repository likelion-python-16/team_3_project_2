import re

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class ResidentPopulation(models.Model):
    rp_key = models.AutoField(primary_key=True)
    total_population = models.PositiveIntegerField()
    population_per_ages = models.PositiveIntegerField()
    income_avg = models.PositiveIntegerField()
    rent_avg = models.PositiveIntegerField()
    traffic_level = models.CharField(max_length=50)

    def __str__(self):
        return f"RP {self.rp_key}"


class CafeId(models.Model):
    cafe_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=140)

    city = models.CharField(max_length=50, default="서울특별시", editable=False)
    distinct = models.CharField(
        max_length=100, help_text="구 단위로 입력하세요 ex) 강남구"
    )
    detail_address = models.CharField(max_length=200, help_text="세부주소를 입력하세요")

    franchise = models.BooleanField(default=False)
    franchise_type = models.CharField(max_length=50, blank=True)
    biz_code = models.CharField(max_length=50, blank=True)

    latitude = models.FloatField()
    longitude = models.FloatField()
    rp_key = models.ForeignKey(
        ResidentPopulation, on_delete=models.PROTECT, related_name="cafes"
    )

    def __str__(self):
        return self.name


class CafeSales(models.Model):
    sales_id = models.AutoField(primary_key=True)

    date = models.CharField(
        max_length=7, help_text="YYYY-MM 형식으로 입력 (예: 2025-07)"
    )

    price = models.PositiveIntegerField()
    visitor_count = models.PositiveIntegerField()
    sales = models.PositiveIntegerField()

    cafe = models.ForeignKey(CafeId, on_delete=models.CASCADE, related_name="sales")

    class Meta:
        indexes = [models.Index(fields=["cafe", "date"])]
        constraints = [
            models.UniqueConstraint(fields=["cafe", "date"], name="unique_cafe_date")
        ]

    def clean(self):
        super().clean()

        if self.date:
            # YYYY-MM 형식 검사
            if not re.match(r"^(20[0-9]{2})-(0[1-9]|1[0-2])$", self.date):
                raise ValidationError(
                    "날짜는 YYYY-MM 형식으로 입력해야 합니다. (예: 2025-07)"
                )

            # 날짜 파싱
            try:
                year, month = map(int, self.date.split("-"))
            except ValueError:
                raise ValidationError("유효하지 않은 날짜 형식입니다.")

            now = timezone.now()

            # 2000년 1월부터 현재까지만 허용
            if year < 2000:
                raise ValidationError("날짜는 2000년 1월부터 입력 가능합니다.")

            # 현재 날짜 기준 전월까지만 허용
            if now.month == 1:
                max_year_month = f"{now.year-1:04d}-12"
            else:
                max_year_month = f"{now.year:04d}-{now.month-1:02d}"

            if self.date > max_year_month:
                raise ValidationError(
                    f"매출 데이터는 현재 기준 전월({max_year_month})까지만 "
                    f"등록 가능합니다."
                )

    @property
    def aov(self):
        """sales/visitor_count"""
        if self.visitor_count == 0:
            return 0
        return self.sales / self.visitor_count

    def __str__(self):
        return f"{self.cafe} / {self.date}"


class CafeReview(models.Model):
    review_id = models.AutoField(primary_key=True)
    review_score = models.FloatField()
    review_count = models.PositiveIntegerField()
    review_text = models.TextField()
    cafe = models.ForeignKey(CafeId, on_delete=models.CASCADE, related_name="reviews")

    def __str__(self):
        return f"Review {self.review_id}"


class CafeTrendAI(models.Model):
    trend_id = models.AutoField(primary_key=True)
    is_risk_area = models.BooleanField()
    is_trendy = models.BooleanField()
    is_growth_expectation = models.BooleanField()
    recommendation_level = models.PositiveSmallIntegerField()
    predicted_growth_rate = models.FloatField()
    investment_opportunity = models.BooleanField()
    rp_key = models.ForeignKey(
        ResidentPopulation, on_delete=models.CASCADE, related_name="trends"
    )

    def __str__(self):
        return f"Trend {self.trend_id}"
