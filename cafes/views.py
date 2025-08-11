from rest_framework import viewsets, permissions
from .models import ResidentPopulation, CafeIf, CafeSales, CafeReview, CafeTrendAI
from .serializers import (
    ResidentPopulationSerializer, CafeIfSerializer, CafeSalesSerializer,
    CafeReviewSerializer, CafeTrendAISerializer
)

class ResidentPopulationViewSet(viewsets.ModelViewSet):
    queryset = ResidentPopulation.objects.all().order_by("rp_key")
    serializer_class = ResidentPopulationSerializer
    permission_classes = [permissions.AllowAny]

class CafeIfViewSet(viewsets.ModelViewSet):
    queryset = CafeIf.objects.select_related("rp_key").order_by("name")
    serializer_class = CafeIfSerializer
    permission_classes = [permissions.AllowAny]

class CafeSalesViewSet(viewsets.ModelViewSet):
    queryset = CafeSales.objects.select_related("cafe").order_by("-date")
    serializer_class = CafeSalesSerializer
    permission_classes = [permissions.AllowAny]

class CafeReviewViewSet(viewsets.ModelViewSet):
    queryset = CafeReview.objects.select_related("cafe").order_by("-review_id")
    serializer_class = CafeReviewSerializer
    permission_classes = [permissions.AllowAny]

class CafeTrendAIViewSet(viewsets.ModelViewSet):
    queryset = CafeTrendAI.objects.select_related("rp_key").order_by("-trend_id")
    serializer_class = CafeTrendAISerializer
    permission_classes = [permissions.AllowAny]
