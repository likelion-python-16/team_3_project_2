from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.shortcuts import render
from django.contrib.auth import authenticate
from django.http import JsonResponse
from .models import User
from .serializers import UserSerializer

def login_page(request):
    """로그인 페이지 렌더링"""
    return render(request, 'login.html')

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
        """사용자 로그인 API"""
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({
                'success': False,
                'message': '이메일과 비밀번호를 입력해주세요.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                if not user.is_active:
                    return Response({
                        'success': False,
                        'message': '비활성화된 계정입니다.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # 토큰 생성 또는 가져오기
                token, created = Token.objects.get_or_create(user=user)
                
                return Response({
                    'success': True,
                    'message': '로그인 성공',
                    'token': token.key,
                    'user': {
                        'id': user.user_id,
                        'username': user.username,
                        'email': user.email,
                        'role': user.role,
                        'is_staff': user.is_staff
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': '잘못된 비밀번호입니다.'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': '존재하지 않는 사용자입니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """사용자 로그아웃 API"""
        try:
            # 토큰 삭제
            token = Token.objects.get(user=request.user)
            token.delete()
            return Response({
                'success': True,
                'message': '로그아웃되었습니다.'
            }, status=status.HTTP_200_OK)
        except Token.DoesNotExist:
            return Response({
                'success': True,
                'message': '로그아웃되었습니다.'
            }, status=status.HTTP_200_OK)
    
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
