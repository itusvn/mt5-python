from ai_models.models import AIModel
from django.db import models
from core.models import Symbol

class TradingStrategy(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    symbol = models.ForeignKey(Symbol, on_delete=models.PROTECT)
    timeframe = models.CharField(max_length=3)  # M1, M5, H1, etc.
    
    # Strategy parameters
    parameters = models.JSONField(default=dict)
    
    # Risk settings 
    risk_per_trade = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[
            MinValueValidator(0.1),
            MaxValueValidator(5.0)
        ]
    )
    max_trades = models.IntegerField(default=5)
    is_active = models.BooleanField(default=True)

    # AI Models
    models = models.ManyToManyField(AIModel, blank=True)
    model_weights = models.JSONField(default=dict)  # Weights for each model's signals
    
    # Performance metrics
    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    total_profit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    class Meta:
        verbose_name_plural = "Trading strategies"
        
    def __str__(self):
        return f"{self.name} - {self.symbol.name} ({self.timeframe})"
        
    @property
    def win_rate(self):
        if self.total_trades == 0:
            return 0
        return (self.winning_trades / self.total_trades) * 100