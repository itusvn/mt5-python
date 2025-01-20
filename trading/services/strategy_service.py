# trading/services/strategy_service.py

from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from django.db.models import Sum, Avg
from django.utils import timezone
from ..models import TradingStrategy, Order
from ai_models.services import ModelService
from core.services import MT5Handler
import logging

logger = logging.getLogger(__name__)

class StrategyService:
    def __init__(self):
        self.mt5 = MT5Handler()
        self.model_service = ModelService()

    def create_strategy(
        self,
        name: str,
        symbol: str,
        timeframe: str,
        parameters: Dict,
        risk_settings: Dict,
        selected_models: List[int],
        model_weights: Optional[Dict] = None
    ) -> TradingStrategy:
        """Create new trading strategy"""
        try:
            # Validate parameters
            if not self._validate_strategy_params(parameters):
                raise ValueError("Invalid strategy parameters")

            # Create strategy
            strategy = TradingStrategy.objects.create(
                name=name,
                symbol_id=symbol,
                timeframe=timeframe,
                parameters=parameters,
                risk_per_trade=risk_settings.get('risk_per_trade', 0.02),
                max_trades=risk_settings.get('max_trades', 5)
            )

            # Add selected models
            strategy.models.add(*selected_models)

            # Set model weights if provided
            if model_weights:
                strategy.model_weights = model_weights
                strategy.save()

            return strategy

        except Exception as e:
            logger.error(f"Error creating strategy: {str(e)}")
            raise

    def _validate_strategy_params(self, parameters: Dict) -> bool:
        """Validate strategy parameters"""
        required_params = ['entry_conditions', 'exit_conditions']
        return all(param in parameters for param in required_params)

    def get_strategy_signals(
        self,
        strategy: TradingStrategy
    ) -> Dict:
        """Get trading signals for strategy"""
        try:
            # Get current market data
            market_data = self.mt5.get_market_data(
                symbol=strategy.symbol.name,
                timeframe=strategy.timeframe
            )

            # Get signals from each model
            model_signals = {}
            for model in strategy.models.filter(active=True):
                signal = self.model_service.get_predictions(
                    model=model,
                    data=market_data
                )
                model_signals[model.id] = signal

            # Aggregate signals using strategy weights
            aggregated_signal = self._aggregate_signals(
                signals=model_signals,
                weights=strategy.model_weights
            )

            # Apply strategy conditions
            final_signal = self._apply_strategy_conditions(
                signal=aggregated_signal,
                conditions=strategy.parameters,
                market_data=market_data
            )

            return final_signal

        except Exception as e:
            logger.error(f"Error getting strategy signals: {str(e)}")
            raise

    def _aggregate_signals(
        self,
        signals: Dict,
        weights: Dict
    ) -> Dict:
        """Aggregate signals from multiple models"""
        aggregated = {
            'BUY': 0,
            'SELL': 0,
            'HOLD': 0
        }

        total_weight = sum(weights.values())

        for model_id, signal in signals.items():
            weight = weights.get(str(model_id), 1)
            aggregated[signal['signal']] += weight

        # Normalize
        for action in aggregated:
            aggregated[action] /= total_weight

        return {
            'signal': max(aggregated.items(), key=lambda x: x[1])[0],
            'confidence': max(aggregated.values()),
            'scores': aggregated
        }

    def _apply_strategy_conditions(
        self,
        signal: Dict,
        conditions: Dict,
        market_data: Dict
    ) -> Dict:
        """Apply additional strategy conditions to signal"""
        entry_conditions = conditions.get('entry_conditions', {})
        exit_conditions = conditions.get('exit_conditions', {})

        # Check entry conditions
        if signal['signal'] in ['BUY', 'SELL']:
            if not self._check_conditions(entry_conditions, market_data):
                signal['signal'] = 'HOLD'
                signal['confidence'] *= 0.5

        # Check exit conditions if in position
        current_position = self._get_current_position(market_data['symbol'])
        if current_position and self._check_conditions(exit_conditions, market_data):
            signal['signal'] = 'CLOSE'
            signal['confidence'] = 1.0

        return signal

    def _check_conditions(
        self,
        conditions: Dict,
        market_data: Dict
    ) -> bool:
        """Check if market data meets conditions"""
        for condition, value in conditions.items():
            if condition == 'rsi':
                if not (value['min'] <= market_data['rsi'] <= value['max']):
                    return False
            elif condition == 'macd':
                if not (market_data['macd'] * value['direction'] > 0):
                    return False
            # Add more conditions as needed

        return True

    def update_strategy_performance(
        self,
        strategy: TradingStrategy,
        order: Order
    ) -> None:
        """Update strategy performance metrics"""
        try:
            strategy.total_trades += 1
            if order.profit > 0:
                strategy.winning_trades += 1
            strategy.total_profit += order.total_profit
            strategy.save()

        except Exception as e:
            logger.error(f"Error updating strategy performance: {str(e)}")
            raise

    def get_strategy_stats(
        self,
        strategy: TradingStrategy,
        days: int = 30
    ) -> Dict:
        """Get strategy performance statistics"""
        try:
            start_date = timezone.now() - timedelta(days=days)
            
            # Get orders for period
            orders = Order.objects.filter(
                models_used__in=strategy.models.all(),
                created_time__gte=start_date
            )

            stats = {
                'total_trades': orders.count(),
                'winning_trades': orders.filter(profit__gt=0).count(),
                'total_profit': orders.aggregate(Sum('profit'))['profit__sum'] or 0,
                'average_profit': orders.filter(profit__gt=0).aggregate(Avg('profit'))['profit__avg'] or 0,
                'average_loss': orders.filter(profit__lt=0).aggregate(Avg('profit'))['profit__avg'] or 0,
                'max_drawdown': self._calculate_drawdown(orders),
                'win_rate': strategy.win_rate,
                'profit_factor': self._calculate_profit_factor(orders),
                'sharpe_ratio': self._calculate_sharpe_ratio(orders),
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting strategy stats: {str(e)}")
            raise

    def _calculate_drawdown(self, orders) -> float:
        """Calculate maximum drawdown"""
        if not orders:
            return 0

        balance = 10000  # Initial balance
        peak = balance
        max_dd = 0

        for order in orders:
            balance += order.total_profit
            if balance > peak:
                peak = balance
            dd = (peak - balance) / peak
            max_dd = max(max_dd, dd)

        return max_dd * 100

    def _calculate_profit_factor(self, orders) -> float:
        """Calculate profit factor"""
        gross_profit = sum(o.profit for o in orders if o.profit > 0) or 0
        gross_loss = abs(sum(o.profit for o in orders if o.profit < 0)) or 1
        return gross_profit / gross_loss

    def _calculate_sharpe_ratio(self, orders, risk_free_rate=0.02) -> float:
        """Calculate Sharpe ratio"""
        if not orders:
            return 0

        returns = [(o.profit / 10000) for o in orders]  # Assuming 10000 initial balance
        avg_return = sum(returns) / len(returns)
        std_dev = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5

        if std_dev == 0:
            return 0

        return (avg_return - risk_free_rate/252) / std_dev * (252 ** 0.5)

    def optimize_strategy(
        self,
        strategy: TradingStrategy,
        parameter_ranges: Dict,
        optimization_target: str = 'sharpe_ratio'
    ) -> Dict:
        """Optimize strategy parameters"""
        # Implementation for strategy optimization
        pass