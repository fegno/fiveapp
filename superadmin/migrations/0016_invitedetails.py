# Generated by Django 3.2.22 on 2023-11-10 06:53

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('superadmin', '0015_moduledetails_module_identifier'),
    ]

    operations = [
        migrations.CreateModel(
            name='InviteDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(blank=True, max_length=100, null=True)),
                ('name', models.CharField(blank=True, max_length=100, null=True)),
                ('is_verified', models.BooleanField(blank=True, default=False)),
                ('is_reject', models.BooleanField(blank=True, default=False)),
                ('is_deleted', models.BooleanField(blank=True, default=False)),
                ('bundle', models.ManyToManyField(blank=True, to='superadmin.BundleDetails')),
                ('module', models.ManyToManyField(blank=True, to='superadmin.ModuleDetails')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
