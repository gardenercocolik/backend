import re
from django.views import View
from django.http import JsonResponse
from django.views import View
from MyModel.models import RecordCompetition

class RecordApproveView(View):
    def post(self, request):
        # 获取 URL 路径
        path = request.path
        # 解析 URL 路径
        match = re.match(r'^/Teacher/record/approve/(?P<id>\d+)/$', path)
        if match:
            # 解析 id
            RecordID = match.group('id')
            # 执行批准操作
            try:
                record = RecordCompetition.objects.get(RecordID=RecordID)
                record.report_competition.status = "approved_record"
                record.save()
                return JsonResponse({'message': '记录已批准', 'id': RecordID})
            except RecordCompetition.DoesNotExist:
                return JsonResponse({'message': '记录不存在', 'id': None})
            except Exception as e:
                return JsonResponse({'message': '更新失败', 'id': None, 'error': str(e)})
        else:
            return JsonResponse({'message': '无效的 URL', 'id': None})