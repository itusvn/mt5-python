# trading/services/execution_service.py
from datetime import timezone
from typing import Dict, Optional
from decimal import Decimal
from core.services import MT5Handler
from ai_models.services import ModelService
from models import Order
import logging

logger = logging.getLogger(__name__)

class ExecutionService:
    def __init__(self):
        self.mt5 = MT5Handler()
        self.model_service = ModelService()

    def execute_order(
        self, 
        symbol: str,
        position_type: str,
        volume: Decimal,
        selected_models: list,
        sl: Optional[Decimal] = None,
        tp: Optional[Decimal] = None
    ) -> Dict:
        """Execute order with AI model signals"""
        try:
            # Get signals from selected models
            signals = self.model_service.get_predictions(symbol, selected_models)
            aggregated_signal = self.model_service.aggregate_signals(signals)

            # Validate signal
            if not self.model_service.validate_signal(aggregated_signal):
                return {
                    'success': False,
                    'error': 'Signal validation failed'
                }

            # Calculate position size
            position_size = self.model_service.get_position_sizing(
                aggregated_signal,
                self.mt5.get_account_info()['balance']
            )

            # Place order
            result = self.mt5.place_order(
                symbol=symbol,
                order_type='MARKET',
                position_type=position_type,
                volume=position_size,
                sl=sl,
                tp=tp
            )

            if result['success']:
                # Create order record
                order = Order.objects.create(
                    symbol_id=symbol,
                    order_type='MARKET',
                    position_type=position_type,
                    volume=position_size,
                    status='OPEN',
                    open_price=result['price'],
                    stop_loss=sl,
                    take_profit=tp,
                    signals=signals
                )
                
                # Add used models
                order.models_used.add(*selected_models)
                
                return {
                    'success': True,
                    'order_id': order.id,
                    'ticket': result['ticket']
                }

            return {
                'success': False,
                'error': result['error']
            }

        except Exception as e:
            logger.error(f"Error executing order: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def close_order(self, order_id: int) -> Dict:
        """Close an open order"""
        try:
            order = Order.objects.get(id=order_id, status='OPEN')
            
            result = self.mt5.close_position(order.ticket)
            
            if result['success']:
                order.status = 'CLOSED'
                order.close_price = result['price']
                order.close_time = timezone.now()
                order.profit = result['profit']
                order.save()
                
                return {
                    'success': True,
                    'profit': order.total_profit
                }

            return {
                'success': False,
                'error': result['error']
            }

        except Order.DoesNotExist:
            return {
                'success': False,
                'error': 'Order not found'
            }
        except Exception as e:
            logger.error(f"Error closing order: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def modify_order(
        self,
        order_id: int,
        sl: Optional[Decimal] = None,
        tp: Optional[Decimal] = None
    ) -> Dict:
        """Modify SL/TP of an open order"""
        try:
            order = Order.objects.get(id=order_id, status='OPEN')
            
            result = self.mt5.modify_position(
                ticket=order.ticket,
                sl=sl,
                tp=tp
            )
            
            if result['success']:
                order.stop_loss = sl
                order.take_profit = tp
                order.save()
                
                return {'success': True}

            return {
                'success': False,
                'error': result['error']
            }

        except Order.DoesNotExist:
            return {
                'success': False,
                'error': 'Order not found'
            }
        except Exception as e:
            logger.error(f"Error modifying order: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }