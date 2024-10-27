from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views import View
from .models import CustomUser, Student, Teacher
from .serializers import CustomUserSerializer
from django.contrib.auth.hashers import make_password
import logging

logger = logging.getLogger('django')

# 注册视图
class RegisterView(View):
    
    def post(self, request):   
        logger.info("Register request received.")     
        try:
            # 直接从 POST 数据中获取字段
            username = request.POST.get('username')
            password = request.POST.get('password')
            identity = request.POST.get('identity')
            email = request.POST.get('email')

            logger.info(f"Register request data: username: {username}, identity: {identity}")

            # 检查用户名是否已存在
            if CustomUser.objects.filter(username=username).exists():
                return JsonResponse({'code': 409, 'error': '用户名已存在！请重新输入！'}, status=409) 

            # 创建用户并加密密码
            user = CustomUser(
                username=username,
                password=make_password(password),
                identity=identity,
                email=email
            )
            user.save()

            # 根据身份创建对应类型的用户记录
            if identity == 'student':
                student_id = request.POST.get('student_id', user.id)  # 如果未提供student_id，则使用user.id
                Student.objects.create(user=user, student_id=student_id)
            elif identity == 'teacher':
                teacher_id = request.POST.get('teacher_id', user.id)  # 如果未提供teacher_id，则使用user.id
                Teacher.objects.create(user=user, teacher_id=teacher_id)
            else:
                user.delete()  # 删除创建的用户以保持数据库的一致性
                return JsonResponse({'code': 400, 'error': '身份值不合法！'}, status=400)

            return JsonResponse({'code': 201, 'message': '注册成功！'}, status=201)

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return JsonResponse({'code': 500, 'error': '服务器内部错误！'}, status=500)

# 登录视图
class LoginView(View):

    def post(self, request):
        try:
            # 直接从 POST 数据中获取字段
            username = request.POST.get('username')
            password = request.POST.get('password')
            identity = request.POST.get('identity')

            logger.info(f"LoginView: {username} login with {identity}")

            if not all([username, password, identity]):
                return JsonResponse({'code': 400, 'error': '缺少必要的字段！'}, status=400)

            # 认证用户
            user = authenticate(request, username=username, password=password)
            if not user:
                logger.warning(f"LoginView: {username} authentication failed.")
                return JsonResponse({'code': 401, 'error': '用户名或密码错误!'}, status=401)

            serializer = CustomUserSerializer(user)
            user_data = serializer.data
            logger.info("user_data: " + str(user_data))

            if (identity == 'student' and user.identity == CustomUser.STUDENT) or \
               (identity == 'teacher' and user.identity == CustomUser.TEACHER):
                login(request, user)
                return JsonResponse({
                    'code': 200,
                    'message': f'{identity} 登录成功!',
                    'user': user_data
                })
            else:
                logger.warning(f"LoginView: {username} identity mismatch.")
                return JsonResponse({'code': 403, 'error': '身份不匹配!'}, status=403)

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return JsonResponse({'code': 500, 'error': '服务器内部错误!'}, status=500)

# 登出视图        
class LogoutView(View):
    def post(self, request):
        try:
            session_key = request.session.session_key

            if session_key:
                # 将会话数据标记为删除
                request.session.delete()
                # 执行修改操作，确保会话的修改被保存
                request.session.modified = True

            return JsonResponse({
                'code': 200,
                'message': '登出成功'
            })
        
        except Exception as e:
            return JsonResponse({'code': 500, 'error': str(e)})  # 确保返回的 error 为字符串形式
