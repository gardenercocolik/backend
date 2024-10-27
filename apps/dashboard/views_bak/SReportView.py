import json
from django.http import JsonResponse
from django.views import View
from django.core.exceptions import ObjectDoesNotExist
from MyModel.models import MainCompetition, ReportCompetition
from Student.unit import check_login, get_user
import logging

# 创建日志器
logger = logging.getLogger('django')



# 处理报备信息
class ReportView(View):
    def post(self, request):
        try:
            # 获取登录用户
            user = get_user(request)
            check_login(user)
            
            # 解析请求体
            data = json.loads(request.body)
            level = data.get("level")
            name = data.get("name")
            competition_start = data.get("competition_start")
            competition_end = data.get("competition_end")
            
            if not all([level, name, competition_start, competition_end]):
                return JsonResponse({'error': '所有字段都是必填的'}, status=400)

            # 根据当前用户获取学生
            student = user.student
            is_other = (level == "other")

            # 获取对应的比赛和负责教师
            try:
                logger.info(f"收到的level: {level}, name: {name}")

                competition = MainCompetition.objects.get(level=level, name=name)

            except MainCompetition.DoesNotExist:
                logger.error(f"没有找到比赛: level={level}, name={name}")
                return JsonResponse({'error': '比赛不存在!'}, status=404)

            try:
                teacher = competition.teacher
            except ObjectDoesNotExist:
                return JsonResponse({'warning': '该比赛没有指定教师!'}, status=404)

            # 创建报备记录
            ReportCompetition.objects.create(
                student=student,
                teacher=teacher,
                level=level,
                name=name,
                is_other=is_other,
                status="pending_report",
                competition_start=competition_start,
                competition_end=competition_end
            )

            return JsonResponse({'status': 'success', 'message': '报备成功!'}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': '请求体必须是合法的JSON！'}, status=400)

        except KeyError:
            return JsonResponse({'error': '缺少必要字段'}, status=400)
