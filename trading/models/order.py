# trading/models/order.py
from django.db import models
from core.models import Symbol
from ai_models.models import AIModel

class Order(models.Model):
    ORDER_TYPES = [
        ('MARKET', 'Market Order'),
        ('LIMIT', 'Limit Order'),
        ('STOP', 'Stop Order')
    ]

    ORDER_STATUS = [
        ('PENDING', 'Pending'),
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
        ('CANCELLED', 'Cancelled')
    ]

    POSITION_TYPES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell')
    ]

    # Basic order info
    symbol = models.ForeignKey(Symbol, on_delete=models.PROTECT)
    order_type = models.CharField(max_length=10, choices=ORDER_TYPES)
    position_type = models.CharField(max_length=4, choices=POSITION_TYPES)
    volume = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=ORDER_STATUS)

    # Price levels
    open_price = models.DecimalField(max_digits=10, decimal_places=5, null=True)
    close_price = models.DecimalField(max_digits=10, decimal_places=5, null=True)
    stop_loss = models.DecimalField(max_digits=10, decimal_places=5, null=True)
    take_profit = models.DecimalField(max_digits=10, decimal_places=5, null=True)

    # Timestamps
    created_time = models.DateTimeField(auto_now_add=True)
    open_time = models.DateTimeField(null=True)
    close_time = models.DateTimeField(null=True)

    # Results
    profit = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    swap = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # AI Models used
    models_used = models.ManyToManyField(AIModel, related_name='trades')
    signals = models.JSONField(default=dict)  # Store signals from each model

    # Additional info
    comment = models.CharField(max_length=255, blank=True)
    magic_number = models.IntegerField(null=True)

    class Meta:
        ordering = ['-created_time']

    def __str__(self):
        return f"{self.symbol.name} {self.position_type} {self.volume}"

    @property
    def total_profit(self):
        if self.profit is None:
            return None
        return self.profit - self.commission + self.swap
