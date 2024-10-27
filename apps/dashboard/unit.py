from django.http import JsonResponse
import logging

logger = logging.getLogger('django')

@staticmethod
def get_user(request):
    user = request.user
    logger.info(user)
    if user is None:
        # 重定向到登录页面 /login跳转到根目录下的login，login跳转到report/login
        return JsonResponse({'error': '用户未登录!'}, status=401)        
    else:
        if user.identity == "student":
            return user
        else:
            return JsonResponse({'error': '用户不是学生!'}, status=401)
        

@staticmethod
def check_login(user):
    if user is None:
        return JsonResponse({'error': '用户未登录!'}, status=401)
    else:
        if user.identity == "student":
            return user
        else:
            return JsonResponse({'error': '用户不是学生!'}, status=401)
        
