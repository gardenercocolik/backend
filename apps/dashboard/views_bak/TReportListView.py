from django.http import JsonResponse
from django.views import View

from MyModel.models import ReportCompetition
from Teacher.unit import get_user


class ReportListView(View):
    def get(self, request):
        user = get_user(request)
        teacher = user.teacher
        data = ReportCompetition.objects.filter(teacher=teacher)

        reports = []
        for report in data.values():
            reports.append(
                {
                    'name': report['name'],
                    'level': report['level'],
                    "student_id": report['student.student_id'],
                    "student_name": report['student.user.name'],
                    "start_time": report['competition_start'],
                    "end_time": report['competition_end'],
                    "report_date": report['report_date'],
                }
            )

        return JsonResponse({'data': reports})
