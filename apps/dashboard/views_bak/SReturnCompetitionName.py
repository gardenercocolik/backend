import json
from django.http import JsonResponse
from django.views import View

from MyModel.models import MainCompetition
from Student.unit import check_login, get_user

#import logging
#logger = logging.getLogger('django')    

#根据比赛等级返回相应的比赛数据
class ReturnCompetitionNameView(View):
    def post(self, request):
        user = get_user(request)
        check_login(user)
        
        try:
            data = json.loads(request.body) # 解析 JSON 请求体
            level = data.get("level")
            if not level:
                return JsonResponse({'error': '缺少必要的字段!'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'error': '请求体格式不正确!'}, status=400)
        
        competition_names = MainCompetition.objects.filter(level=level).values_list('name', flat=True)  # 获取对应等级的竞赛名
        #logger.info(list(competition_names))  # 输出竞赛名到日志
        
        return JsonResponse({'data': list(competition_names)})  # 返回竞赛名列表
