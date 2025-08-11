from rest_framework import viewsets, permissions
from .models import User
from .serializers import UserSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-user_id")
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
