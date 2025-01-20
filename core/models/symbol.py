# core/models/symbol.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Symbol(models.Model):
    """Model quản lý thông tin cặp tiền"""
    name = models.CharField(max_length=10, unique=True)
    display_name = models.CharField(max_length=50)
    pip_value = models.DecimalField(
        max_digits=10, 
        decimal_places=5,
        validators=[MinValueValidator(0)]
    )
    spread = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        validators=[MinValueValidator(0)]
    )
    min_lot = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    max_lot = models.DecimalField(
        max_digits=7, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    margin_required = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Symbol'
        verbose_name_plural = 'Symbols'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.display_name})"

    def validate_lot_size(self, volume):
        """Validate lot size cho symbol"""
        return self.min_lot <= volume <= self.max_lot