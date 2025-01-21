# consumers.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class PriceConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add("price_updates", self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("price_updates", self.channel_name)

    async def price_update(self, event):
        await self.send_json(event['data'])

class TradeConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add("trade_updates", self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("trade_updates", self.channel_name)

    async def trade_update(self, event):
        await self.send_json(event['data'])