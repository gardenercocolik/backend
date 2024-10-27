from django.http import JsonResponse
from django.views import View
from Teacher.unit import get_user
from MyModel.models import ReportCompetition


class RecordListView(View):
    def get(self,request):
        user = get_user(request)
        teacher = user.teacher
        data = ReportCompetition.objects.filter(teacher=teacher)

        reports = []
        for report in data.values():
            reports.append(
                {
                    'ReportID': report['ReportID'],
                    'name': report['name'],
                    'level': report['level'],
                    'report_date': report['report_date'].strftime('%Y-%m-%d %H:%M'),  # 格式化为 YYYY-MM-DD HH:MM
                    'status': report['status']
                }
            )

        return JsonResponse({'data': reports})