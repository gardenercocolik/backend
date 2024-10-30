# Generated by Django 5.1.2 on 2024-10-30 13:43

import dashboard.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecordCompetition',
            fields=[
                ('RecordID', models.AutoField(primary_key=True, serialize=False)),
                ('summary', models.TextField()),
                ('reimbursement_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('submission_time', models.DateTimeField(auto_now_add=True)),
                ('certificate_url', models.URLField(blank=True, null=True)),
                ('photo_url', models.URLField(blank=True, null=True)),
                ('reimbursement_proof_url', models.URLField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProofOfRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('proof', models.ImageField(blank=True, null=True, upload_to=dashboard.models.upload_to_proof, validators=[dashboard.models.RecordCompetition.validate_image_ext, dashboard.models.RecordCompetition.validate_image_size])),
                ('record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.recordcompetition')),
            ],
        ),
        migrations.CreateModel(
            name='PhotoOfRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('photo', models.ImageField(blank=True, null=True, upload_to=dashboard.models.upload_to_photo, validators=[dashboard.models.RecordCompetition.validate_image_ext, dashboard.models.RecordCompetition.validate_image_size])),
                ('record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.recordcompetition')),
            ],
        ),
        migrations.CreateModel(
            name='CertificateOfRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('certificate', models.FileField(blank=True, null=True, upload_to=dashboard.models.upload_to_certificate, validators=[dashboard.models.RecordCompetition.validate_file_ext, dashboard.models.RecordCompetition.validate_file_size])),
                ('record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.recordcompetition')),
            ],
        ),
        migrations.CreateModel(
            name='ReportCompetition',
            fields=[
                ('ReportID', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('level', models.CharField(choices=[('S', 'S'), ('A+', 'A+'), ('A', 'A'), ('B+', 'B+'), ('B', 'B'), ('Other', 'Other')], max_length=10)),
                ('is_other', models.BooleanField(default=False)),
                ('status', models.CharField(choices=[('pending_report', '报备待审核'), ('approved_report', '报备审核通过，待上传竞赛记录'), ('rejected_report', '报备审核不通过'), ('pending_record', '竞赛记录待审核'), ('approved_record', '竞赛记录审核通过'), ('rejected_record', '竞赛记录审核不通过')], default='pending_report', max_length=20)),
                ('report_date', models.DateTimeField(auto_now_add=True)),
                ('competition_start', models.DateTimeField()),
                ('competition_end', models.DateTimeField()),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.student')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.teacher')),
            ],
            options={
                'db_table': 'Reportcompetition',
                'managed': True,
            },
        ),
        migrations.AddField(
            model_name='recordcompetition',
            name='report_competition',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='dashboard.reportcompetition'),
        ),
        migrations.CreateModel(
            name='MainCompetition',
            fields=[
                ('competition_id', models.AutoField(primary_key=True, serialize=False)),
                ('level', models.CharField(choices=[('S', 'S'), ('A+', 'A+'), ('A', 'A'), ('B+', 'B+'), ('B', 'B'), ('Other', 'Other')], max_length=10)),
                ('name', models.CharField(max_length=255)),
                ('teacher', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='users.teacher')),
            ],
            options={
                'db_table': 'Maincompetition',
                'constraints': [models.CheckConstraint(condition=models.Q(('level__in', ['S', 'A+', 'A', 'B+', 'B', 'Other'])), name='valid_level_constraint')],
            },
        ),
        migrations.AddConstraint(
            model_name='reportcompetition',
            constraint=models.CheckConstraint(condition=models.Q(('status__in', ['pending_report', 'approved_report', 'rejected_report', 'pending_record', 'approved_record', 'rejected_record'])), name='valid_status_constraint'),
        ),
        migrations.AddConstraint(
            model_name='reportcompetition',
            constraint=models.CheckConstraint(condition=models.Q(('level__in', ['S', 'A+', 'A', 'B+', 'B', 'Other'])), name='report_valid_level_constraint'),
        ),
    ]
