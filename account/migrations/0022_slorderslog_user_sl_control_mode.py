# Generated by Django 5.1.2 on 2024-11-02 18:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0021_user_quick_exit'),
    ]

    operations = [
        migrations.CreateModel(
            name='slOrderslog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_id', models.CharField(help_text='ID of the Order being traded', max_length=100)),
                ('security_id', models.CharField(help_text='ID of the security being traded', max_length=100)),
                ('exchange_segment', models.CharField(choices=[('NSE', 'National Stock Exchange'), ('BSE', 'Bombay Stock Exchange')], help_text='Segment of the exchange', max_length=50)),
                ('transaction_type', models.CharField(choices=[('BUY', 'Buy'), ('SELL', 'Sell')], default='SELL', max_length=10)),
                ('quantity', models.PositiveIntegerField(help_text='Number of units to trade')),
                ('order_type', models.CharField(choices=[('MARKET', 'Market Order'), ('LIMIT', 'Limit Order'), ('STOP_LOSS', 'Stop Loss Order')], default='STOP_LOSS', max_length=20)),
                ('product_type', models.CharField(choices=[('INTRADAY', 'Intraday'), ('DELIVERY', 'Delivery')], default='INTRADAY', max_length=20)),
                ('price', models.DecimalField(decimal_places=2, help_text='Price at which the order is set', max_digits=10)),
                ('trigger_price', models.DecimalField(decimal_places=2, help_text='Trigger price for stop-loss orders', max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name='user',
            name='sl_control_mode',
            field=models.BooleanField(default=False),
        ),
    ]