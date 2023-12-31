# Generated by Django 3.2.22 on 2023-11-24 02:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0018_freesubscriptiondetails'),
    ]

    operations = [
        migrations.AlterField(
            model_name='moduledetails',
            name='title',
            field=models.CharField(blank=True, choices=[('Team Indicator', 'Team Indicator'), ('Team Workforce Plan Corporate', 'Team Workforce Plan Corporate'), ('Team Cost', 'Team Cost'), ('Payroll Analytics', 'Payroll Analytics'), ('Gender Analytics', 'Gender Analytics'), ('Utility Meter', 'Utility Meter'), ('Sale Center', 'Sale Center'), ('Support', 'Support'), ('Impression', 'Impression'), ('Metrics Meter', 'Metrics Meter'), ('Warehouse MAP Retailing', 'Warehouse MAP Retailing'), ('Logistic Controller', 'Logistic Controller'), ('Odometers', 'Odometers')], max_length=1000, null=True),
        ),
    ]
