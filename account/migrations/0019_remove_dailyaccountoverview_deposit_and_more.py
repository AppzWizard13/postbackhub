# Generated by Django 5.1.2 on 2024-10-28 18:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0018_dailyaccountoverview'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dailyaccountoverview',
            name='deposit',
        ),
        migrations.RemoveField(
            model_name='dailyaccountoverview',
            name='withdrawal',
        ),
    ]
