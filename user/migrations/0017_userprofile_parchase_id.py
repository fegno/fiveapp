# Generated by Django 3.2.21 on 2023-11-15 17:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0016_auto_20231114_1704'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='parchase_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
