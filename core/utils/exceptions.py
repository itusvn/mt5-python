# core/utils/exceptions.py
class TradingBaseException(Exception):
    """Base exception for trading system"""
    pass

class MT5ConnectionError(TradingBaseException):
    """Raised when MT5 connection fails"""
    pass

class OrderExecutionError(TradingBaseException):
    """Raised when order execution fails"""
    pass

class ValidationError(TradingBaseException):
    """Raised when validation fails"""
    def __init__(self, field, message):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")

class MarketDataError(TradingBaseException):
    """Raised when getting market data fails"""
    pass

class RiskCheckError(TradingBaseException):
    """Raised when risk check fails"""
    pass

class InsufficientMarginError(TradingBaseException):
    """Raised when there's not enough margin"""
    pass

class InvalidSymbolError(TradingBaseException):
    """Raised when symbol is invalid"""
    pass

class PositionNotFoundError(TradingBaseException):
    """Raised when position is not found"""
    pass

class DatabaseError(TradingBaseException):
    """Raised when database operation fails"""
    pass