from django.http import JsonResponse
from django.views import View
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from MyModel.models import RecordCompetition, ReportCompetition, ProofOfRecord, PhotoOfRecord, CertificateOfRecord
from Student.unit import get_user
from django.utils import timezone
import logging

from django_project import settings

logger = logging.getLogger(__name__)

class RecordSubmissionView(View):

    def post(self, request):
        user = get_user(request)
        student = user.student
        
        try:
            # 从 POST 数据中获取值
            ReportID = request.POST.get("ReportID")
            reimbursement = request.POST.get("reimbursement")
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
            )
            competition_record.save()  # 保存新创建的对象
            logger.info(f"Created new record for report ID {competition_record.RecordID}")

            # 更新记录的基础字段
            competition_record.submission_time=timezone.now()  # 手动赋值提交时间
            competition_record.summary = summary
            competition_record.reimbursement_amount = reimbursement

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
