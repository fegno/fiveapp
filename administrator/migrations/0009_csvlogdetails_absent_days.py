# Generated by Django 3.2.21 on 2023-09-26 13:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0008_csvlogdetails_extra_hour'),
    ]

    operations = [
        migrations.AddField(
            model_name='csvlogdetails',
            name='absent_days',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
    ]
