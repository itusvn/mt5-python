# apps.py
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class TradingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'trading'

    def ready(self):
        from .trading_app import TradingApplication
        
        # Initialize trading application
        self.trading_app = TradingApplication()
        
        try:
            self.trading_app.start()
        except Exception as e:
            logger.error(f"Failed to start trading application: {e}")