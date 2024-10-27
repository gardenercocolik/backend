from django.http import JsonResponse
from django.views import View
from MyModel.models import CustomUser

from django.shortcuts import get_object_or_404

# 获取用户信息 对应fetchUserInfo
class GetUserInfoView(View):
    def post(self, request):
        user = request.user #获取登录用户
        if user is None:
            return JsonResponse({'error': '用户未登录!'}, status=401)

        user = get_object_or_404(CustomUser, user=user) #判断用户是否存在

        info = {
            'name': user.name,
            'number': user.number,
            'email': user.email,
            'phone': user.phone,
        }

        if any(not value for value in info.values()): #判断用户信息是否完整
            return JsonResponse({'error': '用户信息不完整!', 'data': info}, status=400)

        return JsonResponse({'message': '成功', 'data': info},status=200)

            