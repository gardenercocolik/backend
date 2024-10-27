from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class CustomUser(AbstractUser):  # 用户账号信息，用于登录注册
    STUDENT = 'student'
    TEACHER = 'teacher'
    IDENTITY_CHOICES = [
        (STUDENT, 'Student'),
        (TEACHER, 'Teacher'),
    ]

    identity = models.CharField(max_length=7, choices=IDENTITY_CHOICES, default=STUDENT)  # 身份

    # 重写 groups 和 user_permissions 字段
    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',  # 添加唯一的 related_name
        blank=True,
        help_text='The groups this user belongs to.'
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',  # 添加唯一的 related_name
        blank=True,
        help_text='Specific permissions for this user.'
    )

    def __str__(self):
        return self.username


class Student(models.Model):  # 学生
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True, related_name='student_profile')
    student_id = models.CharField(max_length=10, unique=True, help_text="学生(ID)号，唯一标识学生。")

    class Meta:
        verbose_name = 'Student'
        verbose_name_plural = 'Students'

    def __str__(self):
        return f"{self.user.username} - {self.student_id}"

class Teacher(models.Model):  # 教师
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True, related_name='teacher_profile')
    teacher_id = models.CharField(max_length=10, unique=True, help_text="教师(ID)号，唯一标识教师。")

    class Meta:
        verbose_name = 'Teacher'
        verbose_name_plural = 'Teachers'

    def __str__(self):
        return f"{self.user.username} - {self.teacher_id}"
