# Generated by Django 5.1.2 on 2024-10-20 17:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0003_control_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='control',
            name='is_killed_once',
            field=models.CharField(choices=[('0', 'Disable'), ('1', 'Enable')], default='0', max_length=1),
        ),
        migrations.AlterField(
            model_name='control',
            name='max_order_count_mode',
            field=models.CharField(choices=[('0', 'Disable'), ('1', 'Enable')], default='0', max_length=1),
        ),
        migrations.AlterField(
            model_name='control',
            name='max_profit_mode',
            field=models.CharField(choices=[('0', 'Disable'), ('1', 'Enable')], default='0', max_length=1),
        ),
    ]
