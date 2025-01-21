# trading_app.py
from .services import (
    ExecutionService, 
    ModelService, 
    RealtimeService,
    MT5Service
)

class TradingApplication:
    def __init__(self):
        self.mt5_service = MT5Service()
        self.execution_service = ExecutionService(self.mt5_service)
        self.model_service = ModelService()
        self.realtime_service = RealtimeService()

    def start(self):
        # Connect to MT5
        if not self.mt5_service.connect():
            raise ConnectionError("Failed to connect to MT5")

        # Start price feed
        self.mt5_service.start_price_feed(self.on_price_update)

        # Load AI models
        self.model_service.load_models()

    def on_price_update(self, symbol, price_data):
        # Broadcast price update
        self.realtime_service.broadcast_price_update(symbol, price_data)

        # Get AI predictions
        predictions = self.model_service.get_predictions(symbol, price_data)

        # Update UI with predictions
        self.realtime_service.broadcast_trade_update({
            'type': 'predictions',
            'data': predictions
        })

    def execute_trade(self, trade_request):
        # Execute trade
        result = self.execution_service.execute_trade(trade_request)

        # Broadcast trade result
        self.realtime_service.broadcast_trade_update({
            'type': 'trade_execution',
            'data': result
        })

    def cleanup(self):
        self.mt5_service.disconnect()