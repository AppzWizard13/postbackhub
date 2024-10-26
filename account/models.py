from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    phone_number = models.CharField(max_length=12, null=True)
    profile_image = models.ImageField(upload_to='uploads/', null=True)
    country = models.CharField(max_length=250, null=True)
    status = models.IntegerField(default=0, verbose_name='status', null=True)
    role = models.CharField(max_length=250, null=True)
    dhan_client_id = models.CharField(max_length=250, null=True)
    dhan_access_token = models.CharField(max_length=1000, null=True)
    is_active = models.BooleanField(default=False)  # New is_active field
    auto_stop_loss = models.BooleanField(default=False)
    kill_switch_1  = models.BooleanField(default=False)  # New is_kill_1  field
    kill_switch_2 = models.BooleanField(default=False)  # New is_kill_2  field

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

    max_order_limit = models.IntegerField(default=0)
    peak_order_limit = models.IntegerField(default=0)
    max_loss_limit = models.FloatField(default=0.0)
    max_profit_limit = models.FloatField(default=0.0)
    max_loss_mode = models.CharField(max_length=1, choices=ENABLE_DISABLE_CHOICES, default='0')
    max_profit_mode = models.CharField(max_length=1, choices=ENABLE_DISABLE_CHOICES, default='0')
    max_order_count_mode = models.CharField(max_length=1, choices=ENABLE_DISABLE_CHOICES, default='0')
    stoploss_percentage = models.IntegerField(default=0)
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