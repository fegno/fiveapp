# Generated by Django 3.2.21 on 2023-09-28 06:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0009_csvlogdetails_absent_days'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchasedetails',
            name='parchase_user_type',
            field=models.CharField(blank=True, default='Subscription', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='purchasedetails',
            name='user_count',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]