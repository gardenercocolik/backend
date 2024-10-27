from django.middleware.csrf import get_token
from django.http import JsonResponse

def get_csrf_token(request):
    csrf_token = get_token(request)
    response = JsonResponse({'csrftoken': csrf_token})
    response.set_cookie('csrftoken', csrf_token, httponly=True, samesite='Lax')  # 设置 httponly 和 samesite 属性
    return response

