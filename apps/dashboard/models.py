from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_delete
from django.dispatch import receiver
from users.models import Teacher, Student
import os
import uuid

LEVEL_CHOICES = [
    ('S', 'S'), ('A+', 'A+'), ('A', 'A'),
    ('B+', 'B+'), ('B', 'B'), ('Other', 'Other'),
]

STATUS_CHOICES = [
    ('pending_report', '报备待审核'),
    ('approved_report', '报备审核通过，待上传竞赛记录'),
    ('rejected_report', '报备审核不通过'),
    ('pending_record', '竞赛记录待审核'),
    ('approved_record', '竞赛记录审核通过'),
    ('rejected_record', '竞赛记录审核不通过'),
]


class MainCompetition(models.Model):        
    competition_id = models.AutoField(primary_key=True)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    name = models.CharField(max_length=255)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(level__in=[choice[0] for choice in LEVEL_CHOICES]), name='valid_level_constraint')
        ]

    def __str__(self):
        return self.name


class ReportCompetition(models.Model):      #竞赛报备记录

    ReportID = models.AutoField(primary_key=True)  # 主键
    name = models.CharField(max_length=255)  # 竞赛名称
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)  # 竞赛等级
    is_other = models.BooleanField(default=False)  # 是否是学院规定包含的竞赛
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_report')  # 审核状态
    report_date = models.DateTimeField(auto_now_add=True)  # 报备时间
    competition_start = models.DateTimeField()  # 比赛时间
    competition_end = models.DateTimeField()  # 比赛时间
    instructor = models.CharField(max_length=255, null=True, blank=True)    #指导老师
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)  # 负责老师外键
    student = models.ForeignKey(Student, on_delete=models.CASCADE)  # 报备学生外键

    def clean(self):
        super().clean()
        if self.status not in dict(self.STATUS_CHOICES):
            raise ValidationError(f'Invalid status: {self.status}. Must be one of {self.STATUS_CHOICES}.')
        
    class Meta:
        managed = True
        constraints = [
            models.CheckConstraint(
                check=Q(status__in=[choice[0] for choice in STATUS_CHOICES]),
                name='valid_status_constraint'
            ),
            models.CheckConstraint(
                check=Q(level__in=[choice[0] for choice in LEVEL_CHOICES]),
                name='report_valid_level_constraint'  # 更改名称以反映约束的内容
            ),
        ]

    def __str__(self):
        return f"{self.name} - {self.status}"


def upload_to(instance, filename, subfolder, judge_function):
    ext = filename.split('.')[-1]  # 获取文件扩展名
    if not judge_function(ext):
        raise ValidationError(f"{ext} 不符合文件格式规范。")
    base_filename = os.path.splitext(filename)[0]  # 获取文件名，不包括扩展名
    unique_filename = f"{base_filename}_{uuid.uuid4()}.{ext}"  # 保留原始文件名一部分
    return os.path.join(subfolder, unique_filename)

def upload_to_photo(instance, filename):
    return upload_to(instance, filename, 'competition_photos', RecordCompetition.judge_image_type)

def upload_to_certificate(instance, filename):
    return upload_to(instance, filename, 'competition_certificates', RecordCompetition.judge_image_type)

def upload_to_proof(instance, filename):
    return upload_to(instance, filename, 'reimbursement_proof', RecordCompetition.judge_image_type)

def upload_to_summary(instance, filename):
    return upload_to(instance, filename, 'competition_summaries', RecordCompetition.judge_file_type)

def upload_to_pdf(instance, filename):
    return upload_to(instance, filename, 'competition_pdf', RecordCompetition.judge_pdf_type)


class RecordCompetition(models.Model):      #学生上传竞赛记录库
    
    @staticmethod
    def judge_image_type(ext):
        return ext in ['jpg', 'png', 'jpeg']

    @staticmethod
    def judge_file_type(ext):
        return ext in ['pdf', 'doc', 'docx']
    
    @staticmethod
    def judge_pdf_type(ext):
        return ext == 'pdf'

    def validate_image_ext(self, image):
        ext = image.name.split('.')[-1].lower()
        if not self.judge_image_type(ext):
            raise ValidationError(f"{ext} 不符合图片格式规范。")

    def validate_image_size(self, image):
        if image.size > 10 * 1024 * 1024:  # 10MB
            raise ValidationError('图片大小不能超过10MB。')
        
    def validate_file_ext(self, file):
        ext = file.name.split('.')[-1].lower()
        if not self.judge_file_type(ext):
            raise ValidationError(f"{ext} 不符合文件格式规范。")
        
    def validate_file_size(self, file):
        if file.size > 10 * 1024 * 1024:  # 10MB
            raise ValidationError('文件大小不能超过10MB。')
        
    RecordID = models.AutoField(primary_key=True)  #主键
    report_competition = models.OneToOneField(ReportCompetition, on_delete=models.CASCADE)  # 一对一关系
    summary = models.TextField() # 比赛总结
    reimbursement_amount = models.DecimalField(max_digits=10, decimal_places=2)  # 报销金额
    submission_time = models.DateTimeField(auto_now_add=True)  # 提交时间


    def __str__(self):
        return f"Record of {self.report_competition.name} by {self.report_competition.student.user.username}"
    
#竞赛记录库中的图片和文件
class PhotoOfRecord(models.Model):
    record = models.ForeignKey(RecordCompetition, on_delete=models.CASCADE)  
    photo = models.ImageField(upload_to=upload_to_photo, validators=[RecordCompetition.validate_image_ext, RecordCompetition.validate_image_size],null=True, blank=True)  # 比赛照片，可以不上传

class ProofOfRecord(models.Model):
    record = models.ForeignKey(RecordCompetition, on_delete=models.CASCADE)  
    proof = models.ImageField(upload_to=upload_to_proof, validators=[RecordCompetition.validate_image_ext, RecordCompetition.validate_image_size],null=True, blank=True)  # 比赛照片，可以不上传
    
class CertificateOfRecord(models.Model):
    record = models.ForeignKey(RecordCompetition, on_delete=models.CASCADE)  
    certificate = models.FileField(upload_to=upload_to_certificate,validators=[RecordCompetition.validate_file_ext, RecordCompetition.validate_file_size], null=True, blank=True)  # 证书，可以不上传
@receiver(post_delete, sender=ProofOfRecord)
@receiver(post_delete, sender=PhotoOfRecord)
@receiver(post_delete, sender=CertificateOfRecord)
def delete_file_on_record_delete(instance,record,**kwargs):
    # 针对图片和文件分别检查字段
    file_fields = ['photo', 'proof','certificate']
    for field in file_fields:
        # 检查实例是否有指定的字段，并确保字段不为空
        if hasattr(record, field) and getattr(record, field):
            file_path = getattr(record, field).path
            # 确认文件存在然后删除
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    print(f"Deleted {field} file: {file_path}")
                except Exception as e:
                    print(f"Error deleting {field} file: {file_path} - {e}")
