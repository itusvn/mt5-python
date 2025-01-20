# core/utils/constants.py
from enum import Enum


class TradeType(Enum):
    BUY = "BUY"
    SELL = "SELL"


class TradeStatus(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    ERROR = "ERROR"


class TimeFrame(Enum):
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    M30 = "M30"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"
    W1 = "W1"
    MN1 = "MN1"

    @classmethod
    def get_minutes(cls, timeframe):
        minutes_map = {
            cls.M1: 1,
            cls.M5: 5,
            cls.M15: 15,
            cls.M30: 30,
            cls.H1: 60,
            cls.H4: 240,
            cls.D1: 1440,
            cls.W1: 10080,
            cls.MN1: 43200,
        }
        return minutes_map.get(timeframe)


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# Trading Constants
RISK_SETTINGS = {
    "MAX_DAILY_LOSS": -1000,
    "MAX_POSITION_SIZE": 1.0,
    "MAX_OPEN_POSITIONS": 5,
    "DEFAULT_RISK_PER_TRADE": 0.02,  # 2%
    "MIN_RISK_REWARD_RATIO": 1.5,
    "MAX_SPREAD_POINTS": 20,
}

# MT5 Constants
MT5_SETTINGS = {
    "RETRY_COUNT": 3,
    "RETRY_DELAY": 1,
    "CONNECTION_TIMEOUT": 60000,
    "DEFAULT_DEVIATION": 20,
    "DEFAULT_MAGIC": 123456,
}

# Cache Settings
CACHE_SETTINGS = {
    "MARKET_DATA_TTL": 300,  # 5 minutes
    "SYMBOL_INFO_TTL": 3600,  # 1 hour
    "MAX_CACHED_ITEMS": 1000,
}

# Logging Settings
LOG_SETTINGS = {
    "MAX_FILE_SIZE": 10485760,  # 10MB
    "BACKUP_COUNT": 5,
    "LOG_LEVEL": "INFO",
    "LOG_FORMAT": "%(asctime)s - %(levelname)s - %(message)s",
}
