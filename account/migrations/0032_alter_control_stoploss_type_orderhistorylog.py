# Generated by Django 5.1.2 on 2024-11-15 07:02

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0031_user_last_order_count'),
    ]

    operations = [
        migrations.AlterField(
            model_name='control',
            name='stoploss_type',
            field=models.CharField(choices=[('percentage', 'Percentage'), ('points', 'Points'), ('price', 'Price')], default='percentage', max_length=10),
        ),
        migrations.CreateModel(
            name='OrderHistoryLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_data', models.JSONField()),
                ('date', models.DateField()),
                ('order_count', models.IntegerField()),
                ('profit_loss', models.DecimalField(decimal_places=2, max_digits=10)),
                ('eod_balance', models.DecimalField(decimal_places=2, max_digits=10)),
                ('sod_balance', models.DecimalField(decimal_places=2, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expense', models.DecimalField(decimal_places=2, max_digits=10)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
    ]
