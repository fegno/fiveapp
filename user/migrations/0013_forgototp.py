# Generated by Django 3.2.21 on 2023-10-20 11:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0012_alter_userprofile_user_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='ForgotOTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(blank=True, max_length=100, null=True)),
                ('otp', models.IntegerField()),
                ('is_verified', models.BooleanField(blank=True, default=False)),
            ],
        ),
    ]
