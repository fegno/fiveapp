# Generated by Django 3.2.21 on 2023-09-29 04:41

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('administrator', '0011_cart'),
    ]

    operations = [
        migrations.CreateModel(
            name='AddToCart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count', models.IntegerField(blank=True, default=1, null=True)),
                ('amount', models.FloatField(blank=True, default=0, null=True)),
                ('is_active', models.BooleanField(blank=True, default=False, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now_add=True)),
                ('added_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.DeleteModel(
            name='Cart',
        ),
    ]