# models/ml/feature_engineering.py

import pandas as pd 
import numpy as np
from sklearn.preprocessing import StandardScaler
from typing import List, Dict

class FeatureEngineer:
    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_columns = []
        
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features from raw price data"""
        df = df.copy()
        
        # Technical indicators
        self._add_price_features(df)
        self._add_volume_features(df)
        self._add_trend_features(df) 
        self._add_volatility_features(df)
        self._add_momentum_features(df)
        
        # Drop NaN values
        df = df.dropna()
        
        # Scale features
        self.feature_columns = self._get_feature_columns(df)
        df[self.feature_columns] = self.scaler.fit_transform(df[self.feature_columns])
        
        return df
        
    def _add_price_features(self, df: pd.DataFrame):
        """Add price based features"""
        # Moving averages
        for period in [5, 10, 20, 50, 200]:
            df[f'ma_{period}'] = df['close'].rolling(window=period).mean()
            df[f'ma_{period}_slope'] = df[f'ma_{period}'].pct_change()
            
        # Price changes 
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close']/df['close'].shift(1))
        
        # Price levels
        df['high_low_ratio'] = df['high'] / df['low'] 
        df['close_open_ratio'] = df['close'] / df['open']
        
    def _add_volume_features(self, df: pd.DataFrame):
        """Add volume based features"""
        # Volume changes
        df['volume_ma_5'] = df['volume'].rolling(window=5).mean()
        df['volume_ma_20'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma_20']
        
        # Price-volume
        df['price_volume'] = df['close'] * df['volume']
        df['price_volume_ratio'] = df['price_volume'] / df['price_volume'].rolling(window=20).mean()
        
    def _add_trend_features(self, df: pd.DataFrame):
        """Add trend indicators"""
        # ADX
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['atr'] = true_range.rolling(14).mean()
        
        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
    def _add_volatility_features(self, df: pd.DataFrame):
        """Add volatility indicators"""
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        df['bb_upper'] = df['bb_middle'] + 2*df['close'].rolling(window=20).std()
        df['bb_lower'] = df['bb_middle'] - 2*df['close'].rolling(window=20).std() 
        df['bb_width'] = (df['bb_upper'] - df['bb_lower'])/df['bb_middle']
        
        # Historical volatility
        df['volatility'] = df['returns'].rolling(window=20).std() * np.sqrt(252)
        
    def _add_momentum_features(self, df: pd.DataFrame):
        """Add momentum indicators"""
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100/(1 + rs))
        
        # Stochastic
        low_14 = df['low'].rolling(window=14).min()
        high_14 = df['high'].rolling(window=14).max()
        df['stoch_k'] = 100 * (df['close'] - low_14)/(high_14 - low_14)
        df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
        
    def _get_feature_columns(self, df: pd.DataFrame) -> List[str]:
        """Get list of feature columns"""
        exclude_columns = ['open', 'high', 'low', 'close', 'volume']
        return [col for col in df.columns if col not in exclude_columns]