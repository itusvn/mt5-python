# services/realtime_service.py
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class RealtimeService:
    def __init__(self):
        self.channel_layer = get_channel_layer()

    def broadcast_price_update(self, symbol, price_data):
        async_to_sync(self.channel_layer.group_send)(
            "price_updates",
            {
                "type": "price_update",
                "data": {
                    "symbol": symbol,
                    "bid": price_data['bid'],
                    "ask": price_data['ask'],
                    "timestamp": price_data['timestamp']
                }
            }
        )

    def broadcast_trade_update(self, trade_data):
        async_to_sync(self.channel_layer.group_send)(
            "trade_updates",
            {
                "type": "trade_update",
                "data": trade_data
            }
        )