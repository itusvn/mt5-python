# core/tests/test_mt5_connection.py
from django.test import TestCase
from unittest.mock import patch, MagicMock
from services.mt5_handler import MT5Handler
from utils.exceptions import MT5ConnectionError

class MT5ConnectionTest(TestCase):
    def setUp(self):
        self.mt5_handler = MT5Handler()

    @patch('MetaTrader5.initialize')
    @patch('MetaTrader5.login')
    def test_connection_success(self, mock_login, mock_initialize):
        mock_initialize.return_value = True
        mock_login.return_value = True
        
        self.assertTrue(self.mt5_handler.connect())
        self.assertTrue(self.mt5_handler.connected)

    @patch('MetaTrader5.initialize')
    def test_connection_failure(self, mock_initialize):
        mock_initialize.return_value = False
        
        with self.assertRaises(MT5ConnectionError):
            self.mt5_handler.connect()
            
    def test_reconnection(self):
        self.mt5_handler.connected = False
        self.assertTrue(self.mt5_handler.ensure_connected())