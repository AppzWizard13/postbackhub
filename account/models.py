from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    phone_number = models.CharField(max_length=12, null=True)
    profile_image = models.ImageField(upload_to='uploads/', null=True)
    country = models.CharField(max_length=250, null=True)
    status = models.BooleanField(default=False)  # New is_active field
    role = models.CharField(max_length=250, null=True)
    dhan_client_id = models.CharField(max_length=250, null=True)
    dhan_access_token = models.CharField(max_length=1000, null=True)
    is_active = models.BooleanField(default=False)  # New is_active field
    auto_stop_loss = models.BooleanField(default=False)
    kill_switch_1  = models.BooleanField(default=False)  # New is_kill_1  field
    kill_switch_2 = models.BooleanField(default=False)  # New is_kill_2  field
    quick_exit = models.BooleanField(default=False)
    sl_control_mode = models.BooleanField(default=False)
    last_order_count = models.IntegerField(default=0)
    reserved_trade_count = models.IntegerField(default=0)


    # Adding related_name to prevent reverse accessor clashes
    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_groups',  # Change the related_name to avoid conflict
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_user_permissions',  # Change the related_name to avoid conflict
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username



class Control(models.Model):
    ENABLE_DISABLE_CHOICES = [
        ('0', 'Disable'),
        ('1', 'Enable'),
    ]
    STOPLOSS_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('points', 'Points'),
        ('price', 'Price'),
    ]

    max_order_limit = models.IntegerField(default=0)
    peak_order_limit = models.IntegerField(default=0)
    default_peak_order_limit = models.IntegerField(default=0)
    max_loss_limit = models.FloatField(default=0.0)
    peak_loss_limit = models.FloatField(default=0.0)
    max_profit_limit = models.FloatField(default=0.0)
    peak_profit_limit = models.FloatField(default=0.0)
    max_lot_size_limit = models.FloatField(default=0.0)
    max_loss_mode = models.CharField(max_length=1, choices=ENABLE_DISABLE_CHOICES, default='0')
    max_profit_mode = models.CharField(max_length=1, choices=ENABLE_DISABLE_CHOICES, default='0')
    max_order_count_mode = models.CharField(max_length=1, choices=ENABLE_DISABLE_CHOICES, default='0')
    max_lot_size_mode = models.CharField(max_length=1, choices=ENABLE_DISABLE_CHOICES, default='0')
    stoploss_parameter = models.IntegerField(default=0)
    stoploss_type = models.CharField(
        max_length=10,
        choices=STOPLOSS_TYPE_CHOICES,
        default='percentage',
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Foreign key for user

    def __str__(self):
        return f"Control Settings (Order Limit: {self.max_order_limit}, Profit Limit: {self.max_profit_limit})"



class DhanKillProcessLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_on = models.DateTimeField(default=timezone.now)
    log = models.JSONField()
    order_count = models.IntegerField()

    def __str__(self):
        return f"Log for {self.user.username} - Orders: {self.order_count}"


class TempNotifierTable(models.Model):
    type = models.CharField(max_length=50)  # Adjust max_length as needed
    status = models.BooleanField(default=False)  # Default set to False

    def __str__(self):
        return f"{self.type} - {'Active' if self.status else 'Inactive'}"

class DailyAccountOverview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_account_overviews')
    opening_balance = models.FloatField()
    updated_on = models.DateTimeField(auto_now=True)
    pnl_status = models.FloatField()
    expenses = models.FloatField()
    closing_balance = models.FloatField()
    order_count = models.IntegerField()
    actual_profit = models.FloatField()
    day_open = models.BooleanField(default=False)
    day_close = models.BooleanField(default=False)

    def __str__(self):
        return f"Account Overview for {self.user.username} on {self.updated_on.strftime('%Y-%m-%d')}"


from django.db import models

class slOrderslog(models.Model):
    SECURITY_CHOICES = [
        ('NSE', 'National Stock Exchange'),
        ('BSE', 'Bombay Stock Exchange'),
        # Add more exchanges if needed
    ]
    
    TRANSACTION_CHOICES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]

    PRODUCT_TYPE_CHOICES = [
        ('INTRADAY', 'Intraday'),
        ('DELIVERY', 'Delivery'),
        # Add more product types if needed
    ]

    ORDER_TYPE_CHOICES = [
        ('MARKET', 'Market Order'),
        ('LIMIT', 'Limit Order'),
        ('STOP_LOSS', 'Stop Loss Order'),
        # Add more order types if needed
    ]
    order_id = models.CharField(max_length=100, help_text="ID of the Order being traded")
    security_id = models.CharField(max_length=100, help_text="ID of the security being traded")
    exchange_segment = models.CharField(max_length=50, choices=SECURITY_CHOICES, help_text="Segment of the exchange")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_CHOICES, default='SELL')
    quantity = models.PositiveIntegerField(help_text="Number of units to trade")
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, default='STOP_LOSS')
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES, default='INTRADAY')
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price at which the order is set")
    trigger_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Trigger price for stop-loss orders")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} - {self.transaction_type} {self.quantity} units at {self.price}"





class OrderHistoryLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_data = models.JSONField()
    date = models.DateField()
    order_count = models.IntegerField()
    profit_loss = models.DecimalField(max_digits=10, decimal_places=2)
    eod_balance = models.DecimalField(max_digits=10, decimal_places=2)
    sod_balance = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    expense = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Order History Log for {self.user.username} on {self.date}"

    class Meta:
        ordering = ['-date']

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class DailySelfAnalysis(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    health_check = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], help_text="Rate from 0 to 100")
    mind_check = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], help_text="Rate from 0 to 100")
    expectation_level = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], help_text="Rate from 0 to 100")
    patience_level = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], help_text="Rate from 0 to 100")
    previous_day_self_analysis = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], help_text="Rate from 0 to 100")
    pnl_status = models.CharField(max_length=100, null=True, blank=True, help_text="Profit and Loss Status of the day")
    order_count = models.IntegerField(null=True, blank=True, help_text="Total number of orders of the day")
    date_time = models.DateTimeField(auto_now_add=True, help_text="The date and time when the self-analysis was created")
    overall_advice =  models.CharField(max_length=5000, null=True, blank=True, help_text="Profit and Loss Status of the day")

    def __str__(self):
        return f"Self Analysis on {self.id} by {self.user.username} at {self.date_time}"

from datetime import date
class UserRTCUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=date.today)
    usage_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.date}"