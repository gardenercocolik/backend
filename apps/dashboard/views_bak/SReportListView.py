from django.http import JsonResponse
from django.views import View
from MyModel.models import ReportCompetition
from Student.unit import check_login, get_user
#import logging

#logger = logging.getLogger('django')

# 返回历史报备记录列表
class ReportListView(View):
    def post(self, request):
        user = get_user(request)  # 获取登录用户
        check_login(user)  # 检查登录状态
        student = user.student
        
        # 获取报备记录
        data = ReportCompetition.objects.filter(student=student)

        # 通过自定义序列化处理日期格式
        reports = []
        for report in data.values():
            reports.append({
                'ReportID': report['ReportID'],
                'name': report['name'],
                'level': report['level'],
                'is_other': report['is_other'],
                'status': report['status'],
                'report_date': report['report_date'].strftime('%Y-%m-%d %H:%M'),  # 格式化为 YYYY-MM-DD HH:MM
                'competition_start': report['competition_start'].strftime('%Y-%m-%d %H:%M'),  # 格式化为 YYYY-MM-DD HH:MM
                'competition_end': report['competition_end'].strftime('%Y-%m-%d %H:%M'),  # 格式化为 YYYY-MM-DD HH:MM
                'teacher_id': report['teacher_id'],
                'student_id': report['student_id'],
            })

        #logger.info(f'Retrieved reports: {reports}')
        return JsonResponse({'data': reports})  # 返回报备记录
