from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import User
from .serializers import UserSerializer, RegistrationSerializer

def login_page(request):
    """로그인 페이지 렌더링"""
    return render(request, 'login.html')

def register_page(request):
    """회원가입 페이지 렌더링"""
    return render(request, 'register.html')

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-user_id")
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['get'])
    def template_list(self, request):
        users = self.get_queryset()
        context = {'users': users}
        return render(request, 'accounts/user_list.html', context)
    
    @action(detail=True, methods=['get'])
    def template_detail(self, request, pk=None):
        user = self.get_object()
        context = {'user': user}
        return render(request, 'accounts/user_detail.html', context)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def login(self, request):
        """사용자 로그인 API (세션 기반)"""
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'success': False, 'message': '이메일과 비밀번호를 모두 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, email=email, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return Response({'success': True, 'message': '로그인 성공'})
            else:
                return Response({'success': False, 'message': '비활성화된 계정입니다.'}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'success': False, 'message': '이메일 또는 비밀번호가 올바르지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def register(self, request):
        """사용자 회원가입 API"""
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            login(request, user)
            return Response({'success': True, 'message': '회원가입이 완료되었습니다. 자동으로 로그인됩니다.'}, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        """사용자 로그아웃 API (세션 기반)"""
        logout(request)
        return redirect('/')
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """현재 사용자 정보 조회"""
        if request.user.is_authenticated:
            return Response({
                'success': True,
                'user': {
                    'id': request.user.user_id,
                    'username': request.user.username,
                    'email': request.user.email,
                    'role': request.user.role,
                    'is_staff': request.user.is_staff
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': '인증되지 않은 사용자입니다.'
            }, status=status.HTTP_401_UNAUTHORIZED)
