from rest_framework import serializers
from models import Symbol, Trade, TradingAccount, TradingStrategy

class SymbolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Symbol
        fields = '__all__'

class TradeSerializer(serializers.ModelSerializer):
    symbol_name = serializers.CharField(source='symbol.name', read_only=True)
    total_profit = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Trade
        fields = [
            'id', 'ticket', 'symbol', 'symbol_name',
            'trade_type', 'volume', 'status',
            'open_price', 'close_price', 'sl', 'tp',
            'open_time', 'close_time',
            'profit', 'swap', 'commission', 'total_profit',
            'magic_number', 'comment'
        ]

class OrderRequestSerializer(serializers.Serializer):
    symbol = serializers.CharField()
    type = serializers.ChoiceField(choices=['BUY', 'SELL'])
    volume = serializers.DecimalField(max_digits=7, decimal_places=2)
    sl = serializers.DecimalField(max_digits=10, decimal_places=5, required=False)
    tp = serializers.DecimalField(max_digits=10, decimal_places=5, required=False)
    comment = serializers.CharField(required=False)
    magic = serializers.IntegerField(required=False)

class ModifyOrderSerializer(serializers.Serializer):
    sl = serializers.DecimalField(max_digits=10, decimal_places=5, required=False)
    tp = serializers.DecimalField(max_digits=10, decimal_places=5, required=False)

class AccountSerializer(serializers.ModelSerializer):
    margin_used_percent = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = TradingAccount
        fields = '__all__'

class StrategySerializer(serializers.ModelSerializer):
    win_rate = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = TradingStrategy
        fields = '__all__'