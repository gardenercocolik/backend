import os
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files.base import ContentFile
from django.utils import timezone
import io
from django.http import FileResponse
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from django.core.files.storage import default_storage
from .models import PDFproofOfRecord,ReportCompetition, RecordCompetition, MainCompetition, ProofOfRecord, PhotoOfRecord, CertificateOfRecord

from .models import ReportCompetition, RecordCompetition, MainCompetition, ProofOfRecord, PhotoOfRecord, CertificateOfRecord
from .unit import get_user, check_login

from users.models import CustomUser, Student, Teacher
import os
import json
import logging


URL = "http://localhost:18000"
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
                # logger.info([photo.photo.url for photo in photo])
                certificate = CertificateOfRecord.objects.filter(record=record)
                proof = ProofOfRecord.objects.filter(record=record)

                user = student.user
                # logger.info(photo)
                reports.append({
                    'ReportID': report['ReportID'],
                    'report_date': report['report_date'].strftime('%Y-%m-%d %H:%M'),  # 格式化为 YYYY-MM-DD HH:MM
                    'name': report['name'],
                    'level': report['level'],
                    'status': report['status'],
                    'teacher_id': report['teacher_id'],
                    'instructor': report['instructor'],
                    'student_id': student.student_id,
                    'student_name': user.last_name + user.first_name,
                    'summary': record.summary,
                    'reimbursement_amount': record.reimbursement_amount,
                    'submission_time': record.submission_time.strftime('%Y-%m-%d %H:%M'),  # 格式化为 YYYY-MM-DD HH:MM
                    'photos': [URL + photo.photo.url for photo in photo],
                    'certificate': [URL + certificate.certificate.url for certificate in certificate],
                    'proofs': [URL + proof.proof.url for proof in proof],
                })
                # logger.info(reports)
            except RecordCompetition.DoesNotExist:
                user = student.user
                reports.append({
                    'ReportID': report['ReportID'],
                    'report_date': report['report_date'].strftime('%Y-%m-%d %H:%M'),  # 格式化为 YYYY-MM-DD HH:MM
                    'name': report['name'],
                    'level': report['level'],
                    'status': report['status'],
                    'teacher_id': report['teacher_id'],
                    'instructor': report['instructor'],
                    'student_id': student.student_id,
                    'student_name': user.last_name + user.first_name,
                })
        return JsonResponse({'data': reports})  # 返回报备记录
        

        

# 记录同意
class RecordApproveView(View):
    def post(self, request):
        body = json.loads(request.body)
        ReportID = body.get('ReportID')
        # logger.info(f"收到的参数: {ReportID}")

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
        # logger.info(f"收到的参数: {ReportID}")
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
            # logger.info(f"收到的参数: ReportID={ReportID}, reimbursement={reimbursement}")
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

                return JsonResponse({'message': '记录提交成功!', 'status': 'success'}, status=201)

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
                'instructor': report['instructor'],
                'student_id': student.student_id,
                'student_name': user.last_name + user.first_name
            })

        return JsonResponse({'data': reports})  # 返回报备记录

# 报备同意
class ReportApproveView(View):
    def post(self, request):
        body = json.loads(request.body)
        ReportID = body.get('ReportID')
        # logger.info(f"收到的参数: {ReportID}")

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
        # logger.info(f"收到的参数: {ReportID}")

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
            instructor = request.POST.get("instructor")
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
                instructor=instructor,
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

# 报备删除
class ReportDeleteView(View):
    def post(self, request):
        try:
            # 获取登录用户
            user = get_user(request)
            check_login(user)
            
            # 获取表单数据
            ReportID = request.POST.get("ReportID")
            logger.info(f"收到的ReportID: {ReportID}")
            
            # 根据当前用户获取学生
            student = user.student_profile

            # 根据报备ID获取报备记录
            report_competition = ReportCompetition.objects.get(ReportID=ReportID, student=student)

            # 删除报备记录
            report_competition.delete()

            return JsonResponse({'status': 'success', 'message': '删除成功!'}, status=200)

        except ReportCompetition.DoesNotExist:
            return JsonResponse({'error': '报备记录不存在!'}, status=404)
        
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
                try:
                    student.student_id = userId
                    student.save()
                except:
                    return JsonResponse({'error': '学号已存在!'}, status=400)
            elif user.identity == CustomUser.TEACHER:
                teacher = user.teacher_profile
                try:
                    teacher.teacher_id = userId
                    teacher.save()
                except:
                    return JsonResponse({'error': '教工号已存在!'}, status=400)

            return JsonResponse({'message': '信息更新成功!', 'code': 201})

        except Exception as e:
            return JsonResponse({'error': str(e), 'code': 403})

def generate_pdf_file(ReportID):
        # 获取报备记录
    report_competition = ReportCompetition.objects.get(ReportID=ReportID)
    # 获取竞赛名称
    competition_name = report_competition.name
    # 获取竞赛等级
    competition_level = report_competition.level
    # 获取竞赛开始时间
    competition_start = report_competition.competition_start
    # 获取竞赛结束时间
    competition_end = report_competition.competition_end
    # 获取负责教师
    teacher = report_competition.teacher
    # 获取负责老师的教工号
    teacher_id = teacher.teacher_id
    # 获取负责老师的姓名
    teacher_name = teacher.user.last_name + teacher.user.first_name
    # 获取学生
    student = report_competition.student
    # 获取学生的学号
    student_id = student.student_id
    # 获取学生的姓名
    student_name = student.user.last_name + student.user.first_name
    # 获取记录
    record_competition = RecordCompetition.objects.get(report_competition=report_competition)
    # 获取summary
    summary = record_competition.summary
    # 获取报销金额
    reimbursement = record_competition.reimbursement_amount
    # 获取证书
    certificates = CertificateOfRecord.objects.filter(record=record_competition)
    # 获取照片
    photos = PhotoOfRecord.objects.filter(record=record_competition)
    # 获取报销凭证
    proof = ProofOfRecord.objects.filter(record=record_competition)
    # 创建一个类文件缓冲区以接收PDF数据
    buffer = io.BytesIO()
    # 注册中文字体（假设使用了黑体，确保其路径正确）
    font_path = os.path.join(settings.BASE_DIR, 'static/fonts/SimHei.ttf')  # 替换为你放置字体的实际路径
    pdfmetrics.registerFont(TTFont('SimHei', font_path))
    # 创建PDF对象，使用缓冲区作为其“文件”
    p = canvas.Canvas(buffer)
    p.setFont("SimHei", 12)

    # 绘制文本信息
    y_position = 800  # 初始 Y 轴位置
    info_lines = [
        f"Report ID: {ReportID}",
        f"Competition Name: {competition_name}",
        f"Competition Level: {competition_level}",
        f"Competition Start: {competition_start}",
        f"Competition End: {competition_end}",
        f"Teacher ID: {teacher_id}",
        f"Teacher Name: {teacher_name}",
        f"Student ID: {student_id}",
        f"Student Name: {student_name}",
        f"Summary: {summary}",
        f"Reimbursement Amount: {reimbursement}"
    ]

    for line in info_lines:
        p.drawString(100, y_position, line)
        y_position -= 20  # 每行下移 20 个单位

    # 插入照片
    y_position -= 20  # 留出空间
    p.drawString(100, y_position, "Photos:")
    y_position -= 30  # 照片标题下移
    for photo in photos:
        if photo.photo:  # 确保存在图片
            image_path = default_storage.path(photo.photo.name)
            # 获取图片高度
            img_height = 2 * inch  # 设置图片高度
            p.drawImage(image_path, x=100, y=y_position - img_height, width=2*inch, height=img_height)  # 从左上角绘制图片
            y_position -= img_height + 10  # 下移到下一个图片位置（图片高度 + 间距）
            if y_position < 50:  # 如果快到页面底部，换页
                p.showPage()
                p.setFont("SimHei", 12)
                y_position = 800

    # 插入证书
    y_position -= 20  # 留出空间
    p.drawString(100, y_position, "Certificates:")
    y_position -= 30  # 证书标题下移
    for certificate in certificates:
        if certificate.certificate:  # 确保存在证书
            certificate_path = default_storage.path(certificate.certificate.name)
            img_height = 2 * inch  # 设置证书的高度
            p.drawImage(certificate_path, x=100, y=y_position - img_height, width=2*inch, height=img_height)  # 从左上角绘制证书
            y_position -= img_height + 10  # 下移到下一个证书位置（证书的高度 + 间距）
            if y_position < 50:  # 如果快到页面底部，换页
                p.showPage()
                p.setFont("SimHei", 12)
                y_position = 800
    # 插入报销凭证
    y_position -= 20  # 留出空间
    p.drawString(100, y_position, "Reimbursement Proofs:")
    y_position -= 30  # 凭证标题下移
    for reimbursement_proof in proof:
        if reimbursement_proof.proof:  # 确保存在凭证
            reimbursement_proof_path = default_storage.path(reimbursement_proof.proof.name)
            img_height = 2 * inch  # 设置凭证的高度
            p.drawImage(reimbursement_proof_path, x=100, y=y_position - img_height, width=2*inch, height=img_height)  # 从左上角绘制凭证
            y_position -= img_height + 10  # 下移到下一个凭证位置（凭证的高度 + 间距）
            if y_position < 50:  # 如果快到页面底部，换页
                p.showPage()
                p.setFont("SimHei", 12)
                y_position = 800
    # 妥善关闭PDF对象，完成PDF生成
    p.showPage()
    p.save()

    # 将缓冲区指针重置到开始位置
    buffer.seek(0)
    return buffer

from django.db import transaction
@transaction.atomic
def save_pdf_to_record(record_competition,reportId):
    logger.info(f"开始生成PDF文件")
    pdf_buffer = generate_pdf_file(reportId)
    # 确保为对应记录生成新的 PDFproofOfRecord
    pdf_proof, created = PDFproofOfRecord.objects.get_or_create(record=record_competition)
    pdf_name = f"record_{record_competition.RecordID}.pdf"

    # 保存 PDF 文件
    pdf_proof.pdf.save(pdf_name, ContentFile(pdf_buffer.read()), save=True)
    pdf_buffer.close()

class DownloadPDFView(View):
    def post(self, request, *args, **kwargs):
        ReportID = request.POST.get("ReportID")
        try:
            logger.info(f"收到的ReportID: {ReportID}")
            report_competition = ReportCompetition.objects.get(ReportID=ReportID)
            record_competition = RecordCompetition.objects.get(report_competition=report_competition)
            try:
                pdf=PDFproofOfRecord.objects.get(record=record_competition)
                if pdf.pdf:
                    logger.info("PDF文件已存在")
                    return self.get_pdf_response(pdf)
            except PDFproofOfRecord.DoesNotExist:
                logger.info("PDF文件不存在，将生成新的PDF")
                save_pdf_to_record(record_competition, ReportID)
                pdf=PDFproofOfRecord.objects.get(record=record_competition)
                return self.get_pdf_response(pdf)
        except (ReportCompetition.DoesNotExist, RecordCompetition.DoesNotExist):
            return JsonResponse({'error': '记录不存在!'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'内部错误: {str(e)}'}, status=500)

    def get_pdf_response(self, pdf_record):
    # 构建PDF响应，可以添加适当的逻辑来处理PDF的下载或显示
        response = HttpResponse(pdf_record.pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{pdf_record.pdf.name}"'
        return response
   
class PreviewPDFView(View):
    def post(self, request, *args, **kwargs):
        ReportID = request.POST.get("ReportID")
        try:
            logger.info(f"收到的ReportID: {ReportID}")
            # 获取 report_competition 和 record_competition 对象
            report_competition = ReportCompetition.objects.get(ReportID=ReportID)
            record_competition = RecordCompetition.objects.get(report_competition=report_competition)

            # 检查 PDF 文件是否存在
            try:
                pdf = PDFproofOfRecord.objects.get(record=record_competition)
                if pdf.pdf:
                    logger.info("PDF文件已存在，准备返回")
                    # 返回 PDF 文件进行预览
                    return self.get_pdf_response(pdf)
            except PDFproofOfRecord.DoesNotExist:
                # 如果 PDF 不存在，生成新的 PDF
                logger.info("PDF文件不存在，生成新的PDF")
                save_pdf_to_record(record_competition, ReportID)
                
                # 重新获取刚生成的 PDF 文件
                pdf = PDFproofOfRecord.objects.get(record=record_competition)
                return self.get_pdf_response(pdf)
        
        except (ReportCompetition.DoesNotExist, RecordCompetition.DoesNotExist):
            logger.error("记录不存在!")
            return JsonResponse({'error': '记录不存在!'}, status=404)
        except Exception as e:
            logger.error(f"内部错误: {str(e)}")
            return JsonResponse({'error': f'内部错误: {str(e)}'}, status=500)

    def get_pdf_response(self, pdf_record):
        """返回 PDF 响应以供预览"""
        logger.info(f"返回 PDF 文件: {pdf_record.pdf.name}")
        
        # 返回 PDF 文件内容，并设置为浏览器内联预览
        response = HttpResponse(pdf_record.pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="preview.pdf"'  # inline 允许在浏览器中预览 PDF
        return response