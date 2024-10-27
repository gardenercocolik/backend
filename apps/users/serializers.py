from rest_framework import serializers
from .models import CustomUser, Student, Teacher
  
class CustomUserSerializer(serializers.ModelSerializer):
    student = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all(), required=False)
    teacher = serializers.PrimaryKeyRelatedField(queryset=Teacher.objects.all(), required=False)
  
    class Meta:
        model = CustomUser
        fields = ['username', 'identity', 'student', 'teacher']  # 包含 student 和 teacher 字段
  
class StudentSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()  # 嵌入用户序列化器
  
    class Meta:
        model = Student
        fields = ['user', 'student_id']
  
class TeacherSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()  # 嵌入用户序列化器
  
    class Meta:
        model = Teacher
        fields = ['user', 'teacher_id']