# core/tests/test_market_data.py
from django.test import TestCase
from datetime import datetime, timedelta
from services.market_data import MarketDataManager

class MarketDataTest(TestCase):
    def setUp(self):
        self.market_data = MarketDataManager()

    def test_get_historical_data(self):
        data = self.market_data.get_historical_data(
            symbol='EURUSD',
            timeframe='H1',
            start_date=datetime.now() - timedelta(days=7)
        )
        self.assertIsNotNone(data)
        self.assertTrue(len(data) > 0)

    def test_indicator_calculation(self):
        data = self.market_data.get_historical_data(
            symbol='EURUSD',
            timeframe='H1',
            start_date=datetime.now() - timedelta(days=7),
            include_indicators=True
        )
        self.assertTrue('MA20' in data.columns)
        self.assertTrue('RSI' in data.columns)