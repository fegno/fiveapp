# Generated by Django 3.2.21 on 2023-09-13 15:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0002_auto_20230913_1519'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bundledetails',
            name='modules',
            field=models.ManyToManyField(blank=True, to='superadmin.ModuleDetails'),
        ),
    ]
