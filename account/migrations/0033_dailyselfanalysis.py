# Generated by Django 5.1.2 on 2024-11-21 09:03

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0032_alter_control_stoploss_type_orderhistorylog'),
    ]

    operations = [
        migrations.CreateModel(
            name='DailySelfAnalysis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('health_check', models.IntegerField(help_text='Rate from 0 to 100', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('mind_check', models.IntegerField(help_text='Rate from 0 to 100', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('expectation_level', models.IntegerField(help_text='Rate from 0 to 100', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('patience_level', models.IntegerField(help_text='Rate from 0 to 100', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('previous_day_self_analysis', models.IntegerField(help_text='Rate from 0 to 100', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('pnl_status', models.CharField(blank=True, help_text='Profit and Loss Status of the day', max_length=100, null=True)),
                ('order_count', models.IntegerField(blank=True, help_text='Total number of orders of the day', null=True)),
                ('date_time', models.DateTimeField(auto_now_add=True, help_text='The date and time when the self-analysis was created')),
                ('user', models.ForeignKey(help_text='User who created the self-analysis', on_delete=django.db.models.deletion.CASCADE, related_name='daily_self_analyses', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
