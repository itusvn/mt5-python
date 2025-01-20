# core/models/strategy.py
from django.db import models
import jsonfield
from django.core.validators import MinValueValidator, MaxValueValidator
from .symbol import Symbol

class TradingStrategy(models.Model):
    """Model quản lý chiến lược giao dịch"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    symbol = models.ForeignKey(
        Symbol, 
        on_delete=models.PROTECT,
        related_name='strategies'
    )
    timeframe = models.CharField(max_length=3)  # M1, M5, H1, etc.
    
    # Strategy parameters
    parameters = jsonfield.JSONField()
    
    # Risk settings
    risk_per_trade = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[
            MinValueValidator(0.1),
            MaxValueValidator(5.0)
        ]
    )
    max_trades = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1)]
    )
    is_active = models.BooleanField(default=True)
    
    # Performance metrics
    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    total_profit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    class Meta:
        verbose_name = 'Trading Strategy'
        verbose_name_plural = 'Trading Strategies'
        
    def __str__(self):
        return f"{self.name} - {self.symbol.name} ({self.timeframe})"
        
    @property
    def win_rate(self):
        """Tính tỷ lệ thắng"""
        if self.total_trades == 0:
            return 0
        return (self.winning_trades / self.total_trades) * 100

    def update_stats(self, trade=None):
        """Update statistics khi có trade mới"""
        if trade and trade.status == 'CLOSED':
            self.total_trades += 1
            if trade.profit > 0:
                self.winning_trades += 1
            self.total_profit += trade.total_profit
            self.save()