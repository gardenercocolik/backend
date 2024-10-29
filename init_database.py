import os
import django
from datetime import timedelta
from django.utils import timezone 
from django.contrib.auth.hashers import make_password


# 设置 Django 环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')

# 启动 Django
django.setup()


from dashboard.models import MainCompetition, ReportCompetition
from users.models import CustomUser, Teacher, Student



STATUS_CHOICES = [
    # 报备阶段的状态
    ('pending_report', '报备待审核'),            # 学生提交了竞赛报备，正在等待老师审核
    ('approved_report', '报备审核通过，待上传竞赛记录'),  # 报备审核通过，学生需上传竞赛记录
    ('rejected_report', '报备审核不通过'),         # 报备审核不通过

    # 竞赛记录上传阶段的状态
    ('pending_record', '竞赛记录待审核'),          # 学生已上传竞赛记录，等待老师审核
    ('approved_record', '竞赛记录审核通过'),       # 竞赛记录审核通过，整个流程完成
    ('rejected_record', '竞赛记录审核不通过'),     # 竞赛记录审核不通过
    ]

def bulk_insert_data():
    try:
        levels = ['S', 'A+', 'A', 'B+', 'B', 'Other']     
        reportcompetition_data = []

        for i in range(12):
             # 创建教师用户
            password_hashed =  make_password('!Q2w3e4r') 
            user = CustomUser.objects.create(username=f"tea{i + 1}", password = password_hashed, identity=CustomUser.TEACHER)
            teacher = Teacher.objects.create(user=user, teacher_id=f"T{user.id:03d}")

            # 创建学生用户，确保与教师不同
            student_user = CustomUser.objects.create(username=f"stu{i + 1}", password=password_hashed, identity=CustomUser.STUDENT)
            student = Student.objects.create(user=student_user, student_id=f"S{student_user.id:03d}")

            level = levels[i % len(levels)]  # 循环使用所有等级
            name = f"My-CTF {i + 1}"
            competition = MainCompetition.objects.create(name=name, level=level, teacher=teacher )

            start_date = timezone.now() + timedelta(days=7 * (i + 1))  # 比赛时间以每个比赛为间隔
            end_date = start_date + timedelta(days=2)  # 比赛持续两天
            reportcompetition_data.append(ReportCompetition(
                name=competition.name,
                level=competition.level,
                is_other=(competition.level == 'Other'),
                competition_start=start_date,
                competition_end=end_date,
                teacher=teacher,
                student=student,
                status='pending_report'  
            ))
        
        ReportCompetition.objects.bulk_create(reportcompetition_data)

        print(f"成功插入竞赛")
    except Exception as e:
        print(f"插入失败: {str(e)}")


if __name__ == '__main__':
    bulk_insert_data()
