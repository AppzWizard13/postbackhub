# Generated by Django 5.1.2 on 2024-10-25 10:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0015_alter_control_stoploss_percentage'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='auto_stop_loss',
            field=models.BooleanField(default=False),
        ),
    ]
