# Generated by Django 5.1.2 on 2024-10-24 16:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0014_rename_is_killed_once_control_stoploss_percentage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='control',
            name='stoploss_percentage',
            field=models.IntegerField(default=0),
        ),
    ]
