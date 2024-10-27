from django.http import JsonResponse
from django.views import View

from MyModel.models import ReportCompetition
from Student.unit import get_user


class RecordListView(View):
    def post(self,request):
        user = get_user(request)
        student = user.student
        data = ReportCompetition.objects.filter(student=student)

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

