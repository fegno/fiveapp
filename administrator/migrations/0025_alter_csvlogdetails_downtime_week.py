# Generated by Django 3.2.22 on 2023-11-21 04:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0024_auto_20231119_0930'),
    ]

    operations = [
        migrations.AlterField(
            model_name='csvlogdetails',
            name='downtime_week',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]