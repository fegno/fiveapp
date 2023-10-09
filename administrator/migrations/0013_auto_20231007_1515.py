# Generated by Django 3.2.21 on 2023-10-07 15:15

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('superadmin', '0015_moduledetails_module_identifier'),
        ('administrator', '0012_auto_20230929_1011'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchasedetails',
            name='custom_request',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.CreateModel(
            name='CustomRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=1000, null=True)),
                ('email', models.CharField(blank=True, max_length=1000, null=True)),
                ('phone', models.CharField(blank=True, max_length=1000, null=True)),
                ('subscription_start_date', models.DateField(blank=True, null=True)),
                ('subscription_end_date', models.DateField(blank=True, null=True)),
                ('is_subscribed', models.BooleanField(blank=True, default=True)),
                ('subscription_type', models.CharField(blank=True, max_length=1000, null=True)),
                ('total_price', models.FloatField(default=0)),
                ('status', models.CharField(blank=True, default='Pending', max_length=1000, null=True)),
                ('is_active', models.BooleanField(blank=True, default=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('bundle', models.ManyToManyField(blank=True, to='superadmin.BundleDetails')),
                ('module', models.ManyToManyField(blank=True, to='superadmin.ModuleDetails')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
