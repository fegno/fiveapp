# Generated by Django 3.2.21 on 2023-10-16 08:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0011_carddetails_ccv'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='user_type',
            field=models.CharField(blank=True, choices=[('SUPER_ADMIN', 'Super Admin'), ('ADMIN', 'Admin'), ('USER', 'User')], default='SUPER_ADMIN', max_length=50),
        ),
    ]
