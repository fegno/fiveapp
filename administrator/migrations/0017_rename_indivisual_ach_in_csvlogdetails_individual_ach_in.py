# Generated by Django 3.2.21 on 2023-10-16 08:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0016_auto_20231016_0835'),
    ]

    operations = [
        migrations.RenameField(
            model_name='csvlogdetails',
            old_name='indivisual_ach_in',
            new_name='individual_ach_in',
        ),
    ]
