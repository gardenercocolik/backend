from django.http import JsonResponse
import logging

logger = logging.getLogger('django')

@staticmethod
def get_user(request):
    user = request.user
    logger.info(user)
    if user is None:
        return JsonResponse({'error': '用户未登录!'}, status=401)        
    return user
        

@staticmethod
def check_login(user):
    if user is None:
        return JsonResponse({'error': '用户未登录!'}, status=401)
    return user
