# Generated by Django 3.2.21 on 2023-11-14 17:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0015_delete_invitedetails'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='subscription_end_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='subscription_start_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
