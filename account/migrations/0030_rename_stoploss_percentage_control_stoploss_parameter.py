# Generated by Django 5.1.2 on 2024-11-11 22:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0029_control_stoploss_type'),
    ]

    operations = [
        migrations.RenameField(
            model_name='control',
            old_name='stoploss_percentage',
            new_name='stoploss_parameter',
        ),
    ]
