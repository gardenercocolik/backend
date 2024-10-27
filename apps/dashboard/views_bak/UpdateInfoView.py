import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from MyModel.models import CustomUser


class UpdateInfoView(View):
    def post(self, request):
        user = request.user
        if user is None:
            return JsonResponse({'error': '用户未登录!'}, status=401)

        user = get_object_or_404(CustomUser, user=user)  # 判断用户是否存在
        
        try:
            data = json.loads(request.body)
            name = data.get('name')
            number = data.get('number')
            email = data.get('email')
            phone = data.get('phone')

            user.name = name
            user.number = number
            user.email = email
            user.phone = phone
            user.save()

            return JsonResponse({'message': '信息更新成功!'})

        except Exception as e:
            return JsonResponse({'error': str(e)})