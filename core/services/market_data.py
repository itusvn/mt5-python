# core/services/market_data.py
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from utils.exceptions import MarketDataError
from mt5_handler import MT5Handler
from models.cache import CachedData

import logging

logger = logging.getLogger(__name__)


class MarketDataManager:
    def __init__(self):
        self.mt5 = MT5Handler()
        self.cache = CachedData()

    def get_historical_data(
        self,
        symbol: str,
        timeframe: int,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        include_indicators: bool = False,
    ) -> Optional[pd.DataFrame]:
        """Lấy dữ liệu lịch sử"""

        try:
            # Check cache in MongoDB
            cached_data = self.cache.get_cached_data(
                symbol, timeframe, start_date, end_date
            )

            if cached_data:
                return pd.DataFrame(cached_data['data'])
            
            if not self.mt5.ensure_connected():
                raise MarketDataError("MT5 not connected")            

            # Get rates from MT5
            rates = mt5.copy_rates_range(
                symbol, timeframe, start_date, end_date or datetime.now()
            )

            if rates is None:
                raise MarketDataError(f"Failed to get rates for {symbol}")

            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df["time"] = pd.to_datetime(df["time"], unit="s")
            df.set_index("time", inplace=True)

            # Add technical indicators
            if include_indicators:
                df = self._add_indicators(df)

            # Cache data in MongoDB
            self.cache.cache_data(
                symbol, timeframe, start_date, end_date, df.to_dict(orient='records')
            )

            return df

        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return None

    def _add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators"""
        try:
            # Moving Averages
            df["MA20"] = df["close"].rolling(window=20).mean()
            df["MA50"] = df["close"].rolling(window=50).mean()
            df["MA200"] = df["close"].rolling(window=200).mean()

            # RSI
            delta = df["close"].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            rs = gain / loss
            df["RSI"] = 100 - (100 / (1 + rs))

            # MACD
            exp1 = df["close"].ewm(span=12, adjust=False).mean()
            exp2 = df["close"].ewm(span=26, adjust=False).mean()
            df["MACD"] = exp1 - exp2
            df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
            df["MACD_Hist"] = df["MACD"] - df["Signal"]

            # Bollinger Bands
            df["BB_middle"] = df["close"].rolling(window=20).mean()
            df["BB_upper"] = df["BB_middle"] + 2 * df["close"].rolling(window=20).std()
            df["BB_lower"] = df["BB_middle"] - 2 * df["close"].rolling(window=20).std()

            return df

        except Exception as e:
            logger.error(f"Error adding indicators: {e}")
            return df

    def get_market_depth(self, symbol: str) -> Optional[Dict]:
        """Get market depth"""
        try:
            if not self.mt5.ensure_connected():
                raise MarketDataError("MT5 not connected")

            depth = mt5.market_book_get(symbol)
            if depth is None:
                raise MarketDataError(f"Failed to get market depth for {symbol}")

            asks = []
            bids = []

            for item in depth:
                if item.type == mt5.BOOK_TYPE_SELL:
                    asks.append({"price": item.price, "volume": item.volume})
                elif item.type == mt5.BOOK_TYPE_BUY:
                    bids.append({"price": item.price, "volume": item.volume})

            return {
                "symbol": symbol,
                "asks": asks,
                "bids": bids,
                "timestamp": datetime.now(),
            }

        except Exception as e:
            logger.error(f"Error getting market depth: {e}")
            return None
