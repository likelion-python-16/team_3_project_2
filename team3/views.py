from django.http import HttpResponse


def health_check(request):
    """단순히 HTTP 200 응답과 'OK' 텍스트를 반환하는 헬스 체크 뷰"""
    return HttpResponse("OK")
