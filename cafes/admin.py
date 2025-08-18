from django.contrib import admin
from django import forms
from .models import ResidentPopulation, CafeId, CafeSales, CafeReview, CafeTrendAI

@admin.register(ResidentPopulation)
class ResidentPopulationAdmin(admin.ModelAdmin):
    list_display = ("rp_key", "total_population", "population_per_ages", "income_avg", "rent_avg", "traffic_level")
    list_filter = ("traffic_level",)
    search_fields = ("rp_key",)
    ordering = ("rp_key",)

@admin.register(CafeId)
class CafeIdAdmin(admin.ModelAdmin):
    list_display = ("cafe_id", "name","city","distinct", "detail_address", "biz_code", "latitude", "longitude", "rp_key")
    search_fields = ("name","city","distinct", "detail_address", "biz_code")
    autocomplete_fields = ("rp_key",)
    ordering = ("name",)

@admin.register(CafeSales)
class CafeSalesAdmin(admin.ModelAdmin):
    list_display = ("sales_id", "cafe", "date", "price", "visitor_count", "aov", "sales")
    list_filter = ("cafe", "date")
    search_fields = ("cafe__name",)
    autocomplete_fields = ("cafe",)
    ordering = ("-date",)
    
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'date':
            kwargs['widget'] = forms.TextInput(attrs={'placeholder': '2025-07'})
        return super().formfield_for_dbfield(db_field, request, **kwargs)

@admin.register(CafeReview)
class CafeReviewAdmin(admin.ModelAdmin):
    list_display = ("review_id", "cafe", "review_score", "review_count")
    search_fields = ("cafe__name", "review_text")
    autocomplete_fields = ("cafe",)
    ordering = ("-review_id",)

@admin.register(CafeTrendAI)
class CafeTrendAIAdmin(admin.ModelAdmin):
    list_display = ("trend_id", "rp_key", "is_risk_area", "is_trendy", "is_growth_expectation",
                    "recommendation_level", "predicted_growth_rate", "investment_opportunity")
    list_filter = ("is_risk_area", "is_trendy", "investment_opportunity")
    search_fields = ("rp_key__rp_key",)
    autocomplete_fields = ("rp_key",)
    ordering = ("-trend_id",)
