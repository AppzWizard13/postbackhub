# Generated by Django 5.1.2 on 2024-12-01 04:13

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0038_control_default_peak_order_limit'),
    ]

    operations = [
        migrations.CreateModel(
            name='TradingPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plan_name', models.CharField(max_length=255)),
                ('initial_capital', models.DecimalField(decimal_places=2, max_digits=12)),
                ('expected_growth', models.DecimalField(decimal_places=2, help_text='Expected growth as a percentage (e.g., 15.5 for 15.5%)', max_digits=5)),
                ('no_of_weeks', models.PositiveIntegerField()),
                ('average_weekly_gain', models.DecimalField(decimal_places=2, help_text='Average weekly gain as a percentage (e.g., 2.5 for 2.5%)', max_digits=5)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trading_plans', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='WeeklyGoalReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plan_name', models.CharField(max_length=255)),
                ('week_number', models.IntegerField()),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('accumulated_capital', models.DecimalField(decimal_places=2, max_digits=15)),
                ('gained_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('progress', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('is_achieved', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='DailyGoalReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day_number', models.IntegerField()),
                ('date', models.DateField()),
                ('capital', models.DecimalField(decimal_places=2, max_digits=15)),
                ('gained_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('is_achieved', models.BooleanField(default=False)),
                ('progress', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('weekly_goal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daily_reports', to='account.weeklygoalreport')),
            ],
        ),
    ]
