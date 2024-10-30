from django.http import JsonResponse
from django.views import View
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils import timezone

from .models import ReportCompetition, RecordCompetition, MainCompetition, ProofOfRecord, PhotoOfRecord, CertificateOfRecord
from .unit import get_user, check_login


from users.models import CustomUser, Student, Teacher
import json
import logging

logger = logging.getLogger("django")

# 记录列表
class RecordListView(View):
    def post(self, request):
        user = get_user(request)  # 获取登录用户
        check_login(user)  # 检查登录状态

        if user.identity == CustomUser.STUDENT:
            # 使用新建立的关系
            try:
                student = user.student_profile  # 使用 'student_profile' 获取对应的学生
                data = ReportCompetition.objects.filter(student=student)
            except Student.DoesNotExist:
                return JsonResponse({'error': '该用户没有关联的学生档案'}, status=404)
        elif user.identity == CustomUser.TEACHER:
            try:
                teacher = user.teacher_profile
                data = ReportCompetition.objects.filter(teacher=teacher)
            except Teacher.DoesNotExist:
                return JsonResponse({'error': '该用户没有关联的教师档案'}, status=404)
        
        reports = []  # 初始化报备记录列表
        for report in data.values():
            student = Student.objects.get(user_id=report['student_id'])
            try:
                record = RecordCompetition.objects.get(report_competition=report['ReportID'])
                photo = PhotoOfRecord.objects.filter(record=record)
                certificate = CertificateOfRecord.objects.filter(record=record)
                proof = ProofOfRecord.objects.filter(record=record)

                user = student.user
                logger.info(photo)
                reports.append({
                    'ReportID': report['ReportID'],
                    'report_date': report['report_date'].strftime('%Y-%m-%d %H:%M'),  # 格式化为 YYYY-MM-DD HH:MM
                    'name': report['name'],
                    'level': report['level'],
                    'status': report['status'],
                    'teacher_id': report['teacher_id'],
                    'student_id': student.student_id,
                    'student_name': user.last_name + user.first_name,
                    'summary': record.summary,
                    'reimbursement_amount': record.reimbursement_amount,
                    'submission_time': record.submission_time.strftime('%Y-%m-%d %H:%M'),  # 格式化为 YYYY-MM-DD HH:MM
                    'photos': [photo.photo.url for photo in photo],
                    'certificate': [certificate.certificate.url for certificate in certificate],
                    'proofs': [proof.proof.url for proof in proof],
                })
                logger.info(reports)
            except RecordCompetition.DoesNotExist:
                user = student.user
                reports.append({
                    'ReportID': report['ReportID'],
                    'report_date': report['report_date'].strftime('%Y-%m-%d %H:%M'),  # 格式化为 YYYY-MM-DD HH:MM
                    'name': report['name'],
                    'level': report['level'],
                    'status': report['status'],
                    'teacher_id': report['teacher_id'],
                    'student_id': student.student_id,
                    'student_name': user.last_name + user.first_name,
                })
        return JsonResponse({'data': reports})  # 返回报备记录
        

        

# 记录同意
class RecordApproveView(View):
    def post(self, request):
        body = json.loads(request.body)
        ReportID = body.get('ReportID')
        logger.info(f"收到的参数: {ReportID}")

        # 执行批准操作
        try:
            report = ReportCompetition.objects.get(ReportID=ReportID)
            report.status = "approved_record"
            report.save()
            return JsonResponse({'message': '记录已批准', 'id': ReportID})
        except ReportCompetition.DoesNotExist:
            return JsonResponse({'message': '记录不存在', 'id': None})
        except Exception as e:
            return JsonResponse({'message': '更新失败', 'id': None, 'error': str(e)})   
        
# 记录拒绝  
class RecordRejectView(View):
    def post(self, request):
        body = json.loads(request.body)
        ReportID = body.get('ReportID')
        logger.info(f"收到的参数: {ReportID}")
        # 执行批准操作
        try:
            report = ReportCompetition.objects.get(ReportID=ReportID)
            report.status = "rejected_record"
            report.save()
            return JsonResponse({'message': '记录已拒绝', 'id': ReportID})
        except RecordCompetition.DoesNotExist:
            return JsonResponse({'message': '记录不存在', 'id': None})
        except Exception as e:
            return JsonResponse({'message': '更新失败', 'id': None, 'error': str(e)})


# 记录提交
class RecordSubmitView(View):

    def post(self, request):
        user = get_user(request)
        student = user.student_profile  # 获取对应的学生
        
        try:
            # 从 POST 数据中获取值
            ReportID = request.POST.get("ReportID")
            reimbursement = request.POST.get("reimbursement")
            logger.info(f"收到的参数: ReportID={ReportID}, reimbursement={reimbursement}")
            summary = request.POST.get("summary")

            # 处理上传的文件
            certificates = request.FILES.getlist("certificates")
            photos = request.FILES.getlist("photos")
            proof = request.FILES.getlist("proof")

            # 验证竞赛记录是否存在
            try:
                report_competition = ReportCompetition.objects.get(student=student, ReportID=ReportID)
            except ObjectDoesNotExist:
                return JsonResponse({'error': '该竞赛不存在!'}, status=404)

            # 尝试获取现有的 RecordCompetition，如果已存在则删除记录，包括之前在数据库创建的所有相关图片文件
            try:
                competition_record = RecordCompetition.objects.get(report_competition=report_competition)
                
                # 如果找到该记录，删除它
                competition_record.delete()
                logger.info(f"Deleted existing record with report ID {competition_record.RecordID}")
            except RecordCompetition.DoesNotExist:
                logger.info("No existing record found; creating a new one.")

            # 创建新的 competition_record 对象（无论是否找到并删除了已有记录）
            competition_record = RecordCompetition(
                report_competition=report_competition,
                submission_time=timezone.now(),  # 手动赋值提交时间
                summary = summary,
                reimbursement_amount = reimbursement,
            )
            
            competition_record.save()  # 保存新创建的对象
            competition_record.report_competition.status = "pending_record"
            report_competition.save()
            
            logger.info(f"Created new record for report ID {competition_record.RecordID}")

            

            # 验证文件的扩展名和大小
            def validate_files(files, file_type):
                for file in files:
                    ext = file.name.split('.')[-1].lower()  # 转换为小写
                    logger.info(f"Validating {file.name} with extension {ext}")

                    if file_type == 'image':
                        if not RecordCompetition.judge_image_type(ext):
                            raise ValidationError(f"{ext} 不符合图片格式规范。")
                        if file.size > 10 * 1024 * 1024:
                            raise ValidationError('图片大小不能超过10MB。')
                    elif file_type == 'file':
                        if not RecordCompetition.judge_file_type(ext):
                            raise ValidationError(f"{ext} 不符合文件格式规范。")
                        if file.size > 10 * 1024 * 1024:
                            raise ValidationError('文件大小不能超过10MB。')

            try:
                # 验证证书文件
                validate_files(certificates, 'image')

                # 验证照片文件
                validate_files(photos, 'image')

                # 验证报销凭证文件
                validate_files(proof, 'image')

                # 保存/更新竞赛记录
                competition_record.save()

                logger.info(f"Record saved with ID {competition_record.RecordID}")

                # 保存上传的证书
                for certificate in certificates:
                    CertificateOfRecord.objects.create(record=competition_record, certificate=certificate)

                # 保存上传的照片
                for photo in photos:
                    PhotoOfRecord.objects.create(record=competition_record, photo=photo)

                # 保存报销凭证
                for reimbursement_proof in proof:
                    ProofOfRecord.objects.create(record=competition_record, proof=reimbursement_proof)

                return JsonResponse({'message': '记录提交成功!', 'id': competition_record.RecordID}, status=201)

            except ValidationError as e:
                logger.error(f"Validation error: {str(e)}")
                return JsonResponse({'error': str(e)}, status=400)

        except Exception as e:
            logger.error(f"Error occurred: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

# 报备列表
class ReportListView(View):
    def post(self, request):
        user = get_user(request)  # 获取登录用户
        check_login(user)  # 检查登录状态
        
        if user.identity == CustomUser.STUDENT:
            # 使用新建立的关系
            try:
                student = user.student_profile  # 使用 'student_profile' 获取对应的学生
                data = ReportCompetition.objects.filter(student=student)
            except Student.DoesNotExist:
                return JsonResponse({'error': '该用户没有关联的学生档案'}, status=404)
        elif user.identity == CustomUser. TEACHER:
            try:
                teacher = user.teacher_profile
                data = ReportCompetition.objects.filter(teacher=teacher)
            except Teacher.DoesNotExist:
                return JsonResponse({'error': '该用户没有关联的教师档案'}, status=404)
        

        reports = []  # 初始化报备记录列表

        # 通过自定义序列化处理日期格式
        for report in data.values():
            student = Student.objects.get(user_id=report['student_id'])
            user = student.user
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
                'student_id': student.student_id,
                'student_name': user.last_name + user.first_name
            })

        return JsonResponse({'data': reports})  # 返回报备记录

# 报备同意
class ReportApproveView(View):
    def post(self, request):
        body = json.loads(request.body)
        ReportID = body.get('ReportID')
        logger.info(f"收到的参数: {ReportID}")

        # 执行批准操作
        try:
            report = ReportCompetition.objects.get(ReportID=ReportID)
            report.status = "approved_report"
            report.save()
            return JsonResponse({'message': '记录已批准', 'id': ReportID})
        except ReportCompetition.DoesNotExist:
            return JsonResponse({'message': '记录不存在', 'id': None})
        except Exception as e:
            return JsonResponse({'message': '更新失败', 'id': None, 'error': str(e)})   
         
# 报备拒绝
class ReportRejectView(View):
    def post(self, request):
        body = json.loads(request.body)
        ReportID = body.get('ReportID')
        logger.info(f"收到的参数: {ReportID}")

        # 执行拒绝操作
        try:
            report = ReportCompetition.objects.get(ReportID=ReportID)
            report.status = "rejected_report"
            report.save()
            return JsonResponse({'message': '记录已拒绝', 'id': ReportID})
        except ReportCompetition.DoesNotExist:
            return JsonResponse({'message': '记录不存在', 'id': None})
        except Exception as e:
            return JsonResponse({'message': '更新失败', 'id': None, 'error': str(e)})   

# 报备创建
class ReportCreateView(View):
    def post(self, request):
        try:
            # 获取登录用户
            user = get_user(request)
            check_login(user)
            
            # 获取表单数据
            level = request.POST.get("level")
            name = request.POST.get("name")
            competition_start = request.POST.get("competition_start")
            competition_end = request.POST.get("competition_end")
            
            if not all([level, name, competition_start, competition_end]):
                return JsonResponse({'error': '所有字段都是必填的'}, status=400)

            # 根据当前用户获取学生
            student = user.student_profile

            # 判断是否为其他比赛
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

        except KeyError:
            return JsonResponse({'error': '缺少必要字段'}, status=400)
        
# 根据比赛等级返回相应的比赛数据
class ReturnCompetitionNameView(View):
    def post(self, request):
        user = get_user(request)
        check_login(user)
        
        # 直接通过 request.POST 获取表单数据
        level = request.POST.get("level")
        logger.info(f"收到的level: {level}")
        
        if not level:
            return JsonResponse({'error': '缺少必要的字段!'}, status=400)

        # 获取对应等级的竞赛名
        competition_names = MainCompetition.objects.filter(level=level).values_list('name', flat=True)
        
        return JsonResponse({'data': list(competition_names)})  # 返回竞赛名列表

# 获取用户信息 对应fetchUserInfo
class GetUserInfoView(View):
    def post(self, request):
        #获取登录用户
        user = get_user(request)
        check_login(user)

        info = {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'phone': user.phone,
        }

        if user.identity == CustomUser.STUDENT:
            student = user.student_profile     # 获取对应的学生
            info['userId'] = student.student_id
        elif user.identity == CustomUser.TEACHER:
            teacher = user.teacher_profile     # 获取对应的教师
            info['userId'] = teacher.teacher_id

        # 替换任何空值为 "待输入"
        for key, value in info.items():
            if value is None or value == '':
                info[key] = "待输入"


        return JsonResponse({'message': '成功', 'data': info}, status=200)

class UpdateUserInfoView(View):
    def post(self, request):
        user = get_user(request)
        check_login(user)

        try:
            # 直接从 request.POST 中获取数据
            logger.info(f"收到的参数: {request.POST}")
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            userId = request.POST.get('userId')
            email = request.POST.get('email')
            phone = request.POST.get('phone')

            user.first_name = first_name
            user.last_name= last_name
            user.email = email
            user.phone = phone
            user.save()

            if user.identity == CustomUser.STUDENT:
                student = user.student_profile
                student.student_id = userId
                student.save()
            elif user.identity == CustomUser.TEACHER:
                teacher = user.teacher_profile
                teacher.teacher_id = userId
                teacher.save()

            return JsonResponse({'message': '信息更新成功!', 'code': 201})

        except Exception as e:
            return JsonResponse({'error': str(e)})
