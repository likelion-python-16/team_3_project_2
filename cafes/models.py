from django.db import models

class ResidentPopulation(models.Model):
    rp_key = models.AutoField(primary_key=True)
    total_population = models.PositiveIntegerField()
    population_per_ages = models.PositiveIntegerField()
    income_avg = models.PositiveIntegerField()
    rent_avg = models.PositiveIntegerField()
    traffic_level = models.CharField(max_length=50)

    def __str__(self):
        return f"RP {self.rp_key}"


class CafeIf(models.Model):
    cafe_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=140)
    address = models.CharField(max_length=255)
    biz_code = models.CharField(max_length=50, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    rp_key = models.ForeignKey(ResidentPopulation, on_delete=models.PROTECT, related_name="cafes")

    def __str__(self):
        return self.name


class CafeSales(models.Model):
    sales_id = models.AutoField(primary_key=True)
    date = models.DateTimeField()
    price = models.PositiveIntegerField()
    visitor_count = models.PositiveIntegerField()
    aov = models.DecimalField(max_digits=10, decimal_places=2)
    cafe = models.ForeignKey(CafeIf, on_delete=models.CASCADE, related_name="sales")
    sales = models.PositiveIntegerField()

    class Meta:
        indexes = [models.Index(fields=["cafe", "date"])]

    def __str__(self):
        return f"{self.cafe_id} / {self.date:%Y-%m-%d}"


class CafeReview(models.Model):
    review_id = models.AutoField(primary_key=True)
    review_score = models.FloatField()
    review_count = models.PositiveIntegerField()
    review_text = models.TextField()
    cafe = models.ForeignKey(CafeIf, on_delete=models.CASCADE, related_name="reviews")

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
    rp_key = models.ForeignKey(ResidentPopulation, on_delete=models.CASCADE, related_name="trends")

    def __str__(self):
        return f"Trend {self.trend_id}"
