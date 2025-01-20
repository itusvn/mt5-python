# trading/api/serializers.py

from rest_framework import serializers
from ..models import Order, TradingStrategy

class OrderSerializer(serializers.ModelSerializer):
    total_profit = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = [
            'status', 'open_time', 'close_time',
            'profit', 'swap', 'commission'
        ]

class StrategySerializer(serializers.ModelSerializer):
    win_rate = serializers.FloatField(read_only=True)
    performance_metrics = serializers.SerializerMethodField()

    class Meta:
        model = TradingStrategy
        fields = '__all__'
        read_only_fields = [
            'total_trades', 'winning_trades',
            'total_profit', 'win_rate'
        ]

    def get_performance_metrics(self, obj):
        """Get additional performance metrics"""
        return {
            'win_rate': obj.win_rate,
            'total_profit': float(obj.total_profit),
            'avg_profit_per_trade': float(obj.total_profit / obj.total_trades)
                if obj.total_trades > 0 else 0
        }