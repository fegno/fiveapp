# Generated by Django 3.2.21 on 2024-01-02 15:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0037_auto_20231220_1551'),
    ]

    operations = [
        migrations.AlterField(
            model_name='csvlogdetails',
            name='downtime_week',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
    ]
