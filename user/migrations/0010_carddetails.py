# Generated by Django 3.2.21 on 2023-10-06 08:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0009_billingdetails'),
    ]

    operations = [
        migrations.CreateModel(
            name='CardDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('holder_name', models.CharField(blank=True, max_length=100, null=True)),
                ('card_number', models.CharField(blank=True, max_length=20, null=True)),
                ('expiration_date', models.CharField(blank=True, max_length=5, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
