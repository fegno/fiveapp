# Generated by Django 3.2.21 on 2023-11-19 09:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0023_alter_purchasedetails_action_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='csvlogdetails',
            name='downtime_week',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='csvlogdetails',
            name='factors_effected',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name='csvlogdetails',
            name='impact_hour',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name='csvlogdetails',
            name='system_name',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name='uploadedcsvfiles',
            name='employee_cost_target',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='uploadedcsvfiles',
            name='non_peak_hour_sale_hr',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='uploadedcsvfiles',
            name='non_peak_hour_sale_value',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='uploadedcsvfiles',
            name='peak_hour_sale_hr',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='uploadedcsvfiles',
            name='peak_hour_sale_value',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='uploadedcsvfiles',
            name='sale_target',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
    ]
