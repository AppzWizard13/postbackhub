# Generated by Django 5.1.2 on 2024-11-06 19:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0025_control_max_lot_size_limit'),
    ]

    operations = [
        migrations.AddField(
            model_name='control',
            name='peak_loss_limit',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='control',
            name='peak_profit_limit',
            field=models.FloatField(default=0.0),
        ),
    ]