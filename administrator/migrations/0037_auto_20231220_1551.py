# Generated by Django 3.2.21 on 2023-12-20 15:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0036_auto_20231218_1646'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadedcsvfiles',
            name='automation_100',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='uploadedcsvfiles',
            name='automation_30',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='uploadedcsvfiles',
            name='automation_50',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='uploadedcsvfiles',
            name='automation_75',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
    ]