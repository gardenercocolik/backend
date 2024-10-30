import os
import django
from datetime import timedelta
from django.utils import timezone 

# 设置 Django 环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')

# 启动 Django
django.setup()

from dashboard.models import MainCompetition, ReportCompetition
from users.models import Teacher, Student, CustomUser

def bulk_insert_data():
    try:
        # 获取 CustomUser 对象
        user_id = 1  # 假设这是 CustomUser 的 ID
        user = CustomUser.objects.get(id=user_id)

        student_id = 2023211527
        student = Student.objects.get(student_id=student_id)

        teacher_id = 2023211527
        teacher = Teacher.objects.get(teacher_id=teacher_id)

        levels = ['S', 'A+', 'A', 'B+', 'B']     
        reportcompetition_data = []

        for i in range(10):
            level = levels[i % len(levels)]
            name = f"REAL-CTF {i + 1}"
            competition = MainCompetition.objects.create(name=name, level=level, teacher=teacher)

            start_date = timezone.now() + timedelta(days=7 * (i + 1))
            end_date = start_date + timedelta(days=2)
            
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
        print(f"成功插入 {len(reportcompetition_data)} 个竞赛记录")
    
    except CustomUser.DoesNotExist:
        print(f"用户 ID {user_id} 不存在")
    except Teacher.DoesNotExist:
        print(f"教师对象不存在")
    except Student.DoesNotExist:
        print(f"学生对象不存在")
    except Exception as e:
        print(f"插入失败: {str(e)}")

if __name__ == '__main__':
    bulk_insert_data()
