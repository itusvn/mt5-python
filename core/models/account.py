# core/models/account.py
from django.db import models
from django.core.validators import MinValueValidator

class TradingAccount(models.Model):
    """Model quản lý thông tin tài khoản MT5"""
    account_number = models.IntegerField(unique=True)
    broker = models.CharField(max_length=100)
    currency = models.CharField(max_length=3)
    leverage = models.IntegerField(
        validators=[MinValueValidator(1)]
    )
    is_demo = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    # Account metrics
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    equity = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)] 
    )
    margin = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    free_margin = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    margin_level = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    # Last update
    last_update = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Trading Account'
        verbose_name_plural = 'Trading Accounts'
        ordering = ['-last_update']

    def __str__(self):
        return f"{self.account_number} ({self.broker})"

    def update_metrics(self, metrics):
        """Update account metrics"""
        self.balance = metrics['balance']
        self.equity = metrics['equity']
        self.margin = metrics['margin']
        self.free_margin = metrics['free_margin']
        self.margin_level = metrics['margin_level']
        self.save()

    @property
    def margin_used_percent(self):
        """Tính % margin đã sử dụng"""
        if self.margin == 0:
            return 0
        return (self.margin / self.equity) * 100