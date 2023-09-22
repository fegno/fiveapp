# Generated by Django 3.2.21 on 2023-09-21 15:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0011_userassignedmodules'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('administrator', '0003_auto_20230920_1531'),
    ]

    operations = [
        migrations.CreateModel(
            name='UploadedCsvFiles',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('csv_file', models.FileField(blank=True, null=True, upload_to='')),
                ('standard_working_hour', models.FloatField(blank=True, default=0, null=True)),
                ('is_report_generated', models.BooleanField(blank=True, default=True)),
                ('is_active', models.BooleanField(blank=True, default=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('modules', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='superadmin.moduledetails')),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='CsvLogDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sl_no', models.CharField(blank=True, max_length=1000, null=True)),
                ('working_type', models.CharField(blank=True, max_length=1000, null=True)),
                ('employee_id', models.CharField(blank=True, max_length=1000, null=True)),
                ('employee_name', models.CharField(blank=True, max_length=1000, null=True)),
                ('department', models.CharField(blank=True, max_length=1000, null=True)),
                ('team', models.CharField(blank=True, max_length=1000, null=True)),
                ('designation', models.CharField(blank=True, max_length=1000, null=True)),
                ('working_hour', models.FloatField(blank=True, default=0, null=True)),
                ('is_active', models.BooleanField(blank=True, default=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('uploaded_file', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='administrator.uploadedcsvfiles')),
            ],
        ),
    ]
