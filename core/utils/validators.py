# core/utils/validators.py
from decimal import Decimal
from django.core.exceptions import ValidationError
from exceptions import ValidationError as TradeValidationError

def validate_lot_size(value):
    """Validate trading lot size"""
    if not isinstance(value, (int, float, Decimal)):
        raise ValidationError('Volume must be a number')
    if value <= 0:
        raise ValidationError('Volume must be positive')
        
def validate_price(value):
    """Validate price value"""
    if not isinstance(value, (int, float, Decimal)):
        raise ValidationError('Price must be a number')
    if value <= 0:
        raise ValidationError('Price must be positive')

def validate_sl_tp(order_type, entry_price, sl, tp):
    """Validate Stop Loss and Take Profit levels"""
    if order_type == 'BUY':
        if sl and sl >= entry_price:
            raise TradeValidationError('sl', 'Stop Loss must be below entry price for BUY order')
        if tp and tp <= entry_price:
            raise TradeValidationError('tp', 'Take Profit must be above entry price for BUY order')
    else:  # SELL
        if sl and sl <= entry_price:
            raise TradeValidationError('sl', 'Stop Loss must be above entry price for SELL order')
        if tp and tp >= entry_price:
            raise TradeValidationError('tp', 'Take Profit must be below entry price for SELL order')