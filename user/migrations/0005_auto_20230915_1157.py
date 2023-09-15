# Generated by Django 3.2.21 on 2023-09-15 11:57

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_auto_20230915_1139'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='available_free_users',
            field=models.IntegerField(default=5),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='created_admin',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
