# Generated by Django 3.2.21 on 2023-10-09 16:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0011_carddetails_ccv'),
        ('administrator', '0013_auto_20231007_1515'),
    ]

    operations = [
        migrations.AddField(
            model_name='csvlogdetails',
            name='hourly_rate',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='csvlogdetails',
            name='total_pay',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='purchasedetails',
            name='address',
            field=models.TextField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name='purchasedetails',
            name='bill',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='user.billingdetails'),
        ),
        migrations.AddField(
            model_name='purchasedetails',
            name='billing_contact',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='purchasedetails',
            name='card',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='user.carddetails'),
        ),
        migrations.AddField(
            model_name='purchasedetails',
            name='card_number',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='purchasedetails',
            name='ccv',
            field=models.CharField(blank=True, max_length=3, null=True),
        ),
        migrations.AddField(
            model_name='purchasedetails',
            name='company_name',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
        migrations.AddField(
            model_name='purchasedetails',
            name='expiration_date',
            field=models.CharField(blank=True, max_length=5, null=True),
        ),
        migrations.AddField(
            model_name='purchasedetails',
            name='holder_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='purchasedetails',
            name='issuing_country',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='purchasedetails',
            name='legal_company_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='purchasedetails',
            name='tax_id',
            field=models.CharField(blank=True, max_length=12, null=True),
        ),
        migrations.AddField(
            model_name='uploadedcsvfiles',
            name='monthly_revenue',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.CreateModel(
            name='DepartmentWeightage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('percentage', models.FloatField(blank=True, default=0, null=True)),
                ('is_active', models.BooleanField(blank=True, default=False, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now_add=True)),
                ('uploaded_file', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='administrator.uploadedcsvfiles')),
            ],
        ),
    ]