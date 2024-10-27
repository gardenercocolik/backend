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

def validate_file_type(ext, valid_types):
    """通用文件类型验证"""
    return ext.lower() in valid_types

def generate_upload_path(instance, filename, subfolder, valid_types):
    ext = filename.split('.')[-1].lower()
    if not validate_file_type(ext, valid_types):
        raise ValidationError(f"{ext} 不符合文件格式规范。")
    unique_filename = f"{uuid.uuid4()}_{os.path.splitext(filename)[0]}.{ext}"
    return os.path.join(subfolder, unique_filename)


class MainCompetition(models.Model):        
    competition_id = models.AutoField(primary_key=True)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    name = models.CharField(max_length=255)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, null=True)

    class Meta:
        db_table = 'Maincompetition'
        constraints = [
            models.CheckConstraint(check=Q(level__in=[choice[0] for choice in LEVEL_CHOICES]), name='valid_level_constraint')
        ]

    def __str__(self):
        return self.name


class ReportCompetition(models.Model):      
    ReportID = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    is_other = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_report')
    report_date = models.DateTimeField(auto_now_add=True)
    competition_start = models.DateTimeField()
    competition_end = models.DateTimeField()
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    class Meta:
        db_table = 'Reportcompetition'
        constraints = [
            models.CheckConstraint(check=Q(status__in=[choice[0] for choice in STATUS_CHOICES]), name='valid_status_constraint'),
            models.CheckConstraint(check=Q(level__in=[choice[0] for choice in LEVEL_CHOICES]), name='report_valid_level_constraint')
        ]

    def __str__(self):
        return f"{self.name} - {self.status}"


class RecordCompetition(models.Model):      
    RecordID = models.AutoField(primary_key=True)
    report_competition = models.OneToOneField(ReportCompetition, on_delete=models.CASCADE)
    summary = models.TextField()
    reimbursement_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    submission_time = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def validate_upload(file, valid_types):
        ext = file.name.split('.')[-1].lower()
        if not validate_file_type(ext, valid_types):
            raise ValidationError(f"{ext} 不符合文件格式规范。")
        if file.size > 10 * 1024 * 1024:  # 10MB 限制
            raise ValidationError('文件大小不能超过10MB。')

    class Meta:
        db_table = 'RecordCompetition'

    def __str__(self):
        return f"Record of {self.report_competition.name} by {self.report_competition.student.user.username}"


class FileUploadMixin(models.Model):
    """文件上传混合类，为各文件定义通用的保存逻辑"""
    def save(self, *args, **kwargs):
        file_field = getattr(self, self._meta.get_field('file').name)
        RecordCompetition.validate_upload(file_field, self.valid_types)
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


def upload_photo_path(instance, filename):
    return generate_upload_path(instance, filename, 'competition_photos', ['jpg', 'jpeg', 'png'])

def upload_proof_path(instance, filename):
    return generate_upload_path(instance, filename, 'reimbursement_proof', ['jpg', 'jpeg', 'png'])

def upload_certificate_path(instance, filename):
    return generate_upload_path(instance, filename, 'competition_certificates', ['pdf', 'doc', 'docx'])

class PhotoOfRecord(FileUploadMixin):
    record = models.ForeignKey(RecordCompetition, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to=upload_photo_path)
    valid_types = ['jpg', 'jpeg', 'png']

class ProofOfRecord(FileUploadMixin):
    record = models.ForeignKey(RecordCompetition, on_delete=models.CASCADE)
    proof = models.ImageField(upload_to=upload_proof_path)
    valid_types = ['jpg', 'jpeg', 'png']

class CertificateOfRecord(FileUploadMixin):
    record = models.ForeignKey(RecordCompetition, on_delete=models.CASCADE)
    certificate = models.FileField(upload_to=upload_certificate_path)
    valid_types = ['pdf', 'doc', 'docx']



@receiver(post_delete, sender=ProofOfRecord)
@receiver(post_delete, sender=PhotoOfRecord)
@receiver(post_delete, sender=CertificateOfRecord)
def delete_file_on_record_delete(sender, instance, **kwargs):
    file_field = getattr(instance, instance._meta.get_field('file').name, None)
    if file_field and file_field.path and os.path.isfile(file_field.path):
        try:
            os.remove(file_field.path)
            print(f"Deleted file: {file_field.path}")
        except Exception as e:
            print(f"Error deleting file: {file_field.path} - {e}")
