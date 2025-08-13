from rest_framework import serializers
from .models import ResidentPopulation, CafeId, CafeSales, CafeReview, CafeTrendAI

class ResidentPopulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResidentPopulation
        fields = "__all__"

class CafeIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = CafeId
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
