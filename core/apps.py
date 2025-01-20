# core/apps.py
from django.apps import AppConfig
from django.db.models.signals import post_migrate

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Trading Core'

    def ready(self):
        """
        Initialize app when Django starts
        """
        # Import signal handlers
        from . import signals
        
        # Register post_migrate handler
        post_migrate.connect(self.create_default_data, sender=self)
        
        # Start background tasks
        self.start_background_tasks()
        
    def create_default_data(self, sender, **kwargs):
        """
        Create default data after migrations
        """
        from .models import Symbol
        
        # Create default symbols if none exist
        if not Symbol.objects.exists():
            default_symbols = [
                {
                    'name': 'EURUSD',
                    'display_name': 'EUR/USD',
                    'pip_value': 0.0001,
                    'spread': 1.0,
                    'min_lot': 0.01,
                    'max_lot': 10.0,
                },
                {
                    'name': 'GBPUSD',
                    'display_name': 'GBP/USD',
                    'pip_value': 0.0001,
                    'spread': 1.2,
                    'min_lot': 0.01,
                    'max_lot': 10.0,
                }
            ]
            
            for symbol_data in default_symbols:
                Symbol.objects.create(**symbol_data)
                
    def start_background_tasks(self):
        """
        Start background tasks like market data updates
        """
        try:
            from .tasks import start_market_data_updater
            start_market_data_updater()
        except ImportError:
            pass  # Optional background tasks not available