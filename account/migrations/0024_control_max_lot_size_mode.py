# Generated by Django 5.1.2 on 2024-11-05 08:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0023_alter_user_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='control',
            name='max_lot_size_mode',
            field=models.CharField(choices=[('0', 'Disable'), ('1', 'Enable')], default='0', max_length=1),
        ),
    ]
