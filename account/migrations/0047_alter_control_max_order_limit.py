# Generated by Django 5.1.2 on 2024-12-26 03:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0046_dailygoalreport_plan_name_weeklygoalreport_plan_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='control',
            name='max_order_limit',
            field=models.IntegerField(default=0, null=True),
        ),
    ]
