# Generated by Django 3.2.21 on 2023-09-13 15:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='moduledetails',
            name='monthly_price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=7),
        ),
        migrations.AddField(
            model_name='moduledetails',
            name='weekly_price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=7),
        ),
        migrations.AddField(
            model_name='moduledetails',
            name='yearly_price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=7),
        ),
        migrations.CreateModel(
            name='BundleDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, choices=[('Team Indicator', 'Team Indicator'), ('Team Workforce Plan Corporate', 'Team Workforce Plan Corporate'), ('Team Cost HR Costing and Accounting department', 'Team Cost HR Costing and Accounting department'), ('Payroll Analytics - Business Services', 'Payroll Analytics - Business Services'), ('Gender analytics - Finance and HR department', 'Gender analytics - Finance and HR department'), ('UTILITY METER - SUPPLY CHAIN', 'UTILITY METER - SUPPLY CHAIN'), ('METRICS METER / SALE CENTRE', 'METRICS METER / SALE CENTRE'), ('Warehouse MAP Retail', 'Warehouse MAP Retail'), ('Logistic Controller', 'Logistic Controller'), ('ODOMETERS: BACK OFFICE', 'ODOMETERS: BACK OFFICE')], max_length=1000, null=True)),
                ('weekly_price', models.DecimalField(decimal_places=2, default=0, max_digits=7)),
                ('monthly_price', models.DecimalField(decimal_places=2, default=0, max_digits=7)),
                ('yearly_price', models.DecimalField(decimal_places=2, default=0, max_digits=7)),
                ('is_active', models.BooleanField(blank=True, default=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modules', models.ManyToManyField(blank=True, null=True, to='superadmin.ModuleDetails')),
            ],
        ),
    ]
