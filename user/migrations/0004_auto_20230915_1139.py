# Generated by Django 3.2.21 on 2023-09-15 11:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_auto_20230915_1416'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='free_subscribed',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='free_subscription_end_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='free_subscription_start_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='take_free_subscription',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]