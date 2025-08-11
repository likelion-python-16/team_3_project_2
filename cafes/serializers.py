from rest_framework import serializers
from .models import ResidentPopulation, CafeIf, CafeSales, CafeReview, CafeTrendAI

class ResidentPopulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResidentPopulation
        fields = "__all__"

class CafeIfSerializer(serializers.ModelSerializer):
    class Meta:
        model = CafeIf
        fields = "__all__"

class CafeSalesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CafeSales
        fields = "__all__"

class CafeReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = CafeReview
        fields = "__all__"

class CafeTrendAISerializer(serializers.ModelSerializer):
    class Meta:
        model = CafeTrendAI
        fields = "__all__"
