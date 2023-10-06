# Generated by Django 3.2.21 on 2023-10-06 06:22

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0008_auto_20230919_1444'),
    ]

    operations = [
        migrations.CreateModel(
            name='BillingDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(blank=True, max_length=150, null=True)),
                ('address', models.TextField(blank=True, max_length=1000, null=True)),
                ('billing_contact', models.CharField(blank=True, max_length=100, null=True)),
                ('issuing_country', models.CharField(blank=True, max_length=100, null=True)),
                ('legal_company_name', models.CharField(blank=True, max_length=100, null=True)),
                ('tax_id', models.CharField(blank=True, max_length=12, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]