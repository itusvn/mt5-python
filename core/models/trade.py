# core/models/trade.py
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from .symbol import Symbol

class Trade(models.Model):
    """Model quản lý thông tin giao dịch"""
    TRADE_TYPES = (
        ('BUY', 'Buy'),
        ('SELL', 'Sell')
    )
    
    TRADE_STATUS = (
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'), 
        ('CANCELLED', 'Cancelled'),
        ('ERROR', 'Error')
    )

    # Basic trade info
    ticket = models.IntegerField(unique=True)
    symbol = models.ForeignKey(
        Symbol, 
        on_delete=models.PROTECT,
        related_name='trades'
    )
    trade_type = models.CharField(max_length=4, choices=TRADE_TYPES)
    volume = models.DecimalField(
        max_digits=7, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    status = models.CharField(
        max_length=10, 
        choices=TRADE_STATUS,
        default='OPEN'
    )

    # Price information  
    open_price = models.DecimalField(max_digits=10, decimal_places=5)
    close_price = models.DecimalField(
        max_digits=10, 
        decimal_places=5, 
        null=True, 
        blank=True
    )
    sl = models.DecimalField(
        max_digits=10, 
        decimal_places=5,
        null=True, 
        blank=True
    )
    tp = models.DecimalField(
        max_digits=10, 
        decimal_places=5,
        null=True, 
        blank=True
    )

    # Time information
    open_time = models.DateTimeField(auto_now_add=True)
    close_time = models.DateTimeField(null=True, blank=True)

    # Trade results
    profit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    swap = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    commission = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    # Additional info
    magic_number = models.IntegerField(null=True, blank=True)
    comment = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name = 'Trade'
        verbose_name_plural = 'Trades'
        ordering = ['-open_time']
        indexes = [
            models.Index(fields=['ticket']),
            models.Index(fields=['symbol', 'status'])
        ]

    def __str__(self):
        return f"{self.ticket} - {self.symbol.name} {self.trade_type}"

    @property
    def total_profit(self):
        """Tính tổng profit bao gồm swap và commission"""
        if self.profit is None:
            return None
        return self.profit + self.swap - self.commission

    def close(self, close_price):
        """Đóng lệnh"""
        self.status = 'CLOSED'
        self.close_price = close_price
        self.close_time = timezone.now()
        self.calculate_profit()
        self.save()

    def calculate_profit(self):
        """Tính profit của lệnh"""
        if self.close_price is None:
            return
            
        pip_value = self.symbol.pip_value
        pips = self.close_price - self.open_price
        
        if self.trade_type == 'SELL':
            pips = -pips
            
        self.profit = (pips / pip_value) * self.volume