# Generated by Django 3.2.21 on 2023-09-28 07:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0013_deleteuserslog'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='deleteuserslog',
            name='module',
        ),
        migrations.AddField(
            model_name='deleteuserslog',
            name='module',
            field=models.ManyToManyField(blank=True, null=True, to='superadmin.ModuleDetails'),
        ),
    ]