# core/tests/test_order_execution.py
from django.test import TestCase
from decimal import Decimal
from services.order_manager import OrderManager
from models import Trade, Symbol
from utils.exceptions import OrderExecutionError

class OrderExecutionTest(TestCase):
    def setUp(self):
        self.order_manager = OrderManager()
        self.symbol = Symbol.objects.create(
            name='EURUSD',
            pip_value=Decimal('0.0001'),
            min_lot=Decimal('0.01'),
            max_lot=Decimal('10.0')
        )

    def test_place_market_order(self):
        result = self.order_manager.place_market_order(
            symbol='EURUSD',
            order_type='BUY',
            volume=0.1
        )
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['trade_id'])

    def test_invalid_volume(self):
        with self.assertRaises(OrderExecutionError):
            self.order_manager.place_market_order(
                symbol='EURUSD',
                order_type='BUY',
                volume=20.0  # Exceeds max_lot
            )

    def test_close_position(self):
        trade = Trade.objects.create(
            ticket=12345,
            symbol=self.symbol,
            trade_type='BUY',
            volume=0.1,
            open_price=1.1000
        )
        result = self.order_manager.close_position(trade.ticket)
        self.assertTrue(result['success'])