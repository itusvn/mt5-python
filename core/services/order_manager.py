# core/services/order_manager.py
from typing import Dict, List, Optional
from datetime import datetime
import logging
from models import Trade, Symbol
from mt5_handler import MT5Handler
from utils.exceptions import OrderExecutionError

logger = logging.getLogger(__name__)

class OrderManager:
    def __init__(self):
        self.mt5 = MT5Handler()

    def place_market_order(
        self,
        symbol: str,
        order_type: str,
        volume: float,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        comment: str = "",
        magic: int = 0
    ) -> Dict:
        """Place market order and save to database"""
        try:
            # Place order via MT5
            result = self.mt5.place_order(
                symbol=symbol,
                order_type=order_type,
                volume=volume,
                sl=sl,
                tp=tp,
                comment=comment,
                magic=magic
            )

            if not result['success']:
                raise OrderExecutionError(result['error'])

            # Save trade to database
            symbol_obj = Symbol.objects.get(name=symbol)
            trade = Trade.objects.create(
                ticket=result['ticket'],
                symbol=symbol_obj,
                trade_type=order_type,
                volume=volume,
                open_price=result['price'],
                sl=sl,
                tp=tp,
                magic_number=magic,
                comment=comment
            )

            logger.info(f"Order placed and saved: {trade}")
            return {
                'success': True,
                'trade_id': trade.id,
                'ticket': result['ticket']
            }

        except Exception as e:
            error_msg = f"Error placing order: {e}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}

    def close_position(self, ticket: int) -> Dict:
        """Close position"""
        try:
            # Get trade from database
            trade = Trade.objects.get(ticket=ticket, status='OPEN')

            # Close position via MT5
            result = self.mt5.place_order(
                symbol=trade.symbol.name,
                order_type='SELL' if trade.trade_type == 'BUY' else 'BUY',
                volume=trade.volume,
                comment=f"Close #{ticket}"
            )

            if not result['success']:
                raise OrderExecutionError(result['error'])

            # Update trade in database
            trade.status = 'CLOSED'
            trade.close_price = result['price']
            trade.close_time = datetime.now()
            trade.calculate_profit()
            trade.save()

            logger.info(f"Position closed: {trade}")
            return {'success': True, 'trade_id': trade.id}

        except Exception as e:
            error_msg = f"Error closing position: {e}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}

    def modify_position(
        self,
        ticket: int,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> Dict:
        """Modify position SL/TP"""
        try:
            # Get trade from database
            trade = Trade.objects.get(ticket=ticket, status='OPEN')

            # Modify position via MT5https://claude.ai/chat/f8234915-eeb5-4ff8-98a8-4f013d4b15b0
            result = self.mt5.modify_position(
                ticket=ticket,
                sl=sl,
                tp=tp
            )

            if not result['success']:
                raise OrderExecutionError(result['error'])

            # Update trade in database
            if sl is not None:
                trade.sl = sl
            if tp is not None:
                trade.tp = tp
            trade.save()

            logger.info(f"Position modified: {trade}")
            return {'success': True, 'trade_id': trade.id}

        except Exception as e:
            error_msg = f"Error modifying position: {e}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}

    def get_open_positions(self) -> List[Dict]:
        """Get all open positions"""
        try:
            positions = Trade.objects.filter(status='OPEN').select_related('symbol')
            return [{
                'id': pos.id,
                'ticket': pos.ticket,
                'symbol': pos.symbol.name,
                'type': pos.trade_type,
                'volume': float(pos.volume),
                'open_price': float(pos.open_price),
                'sl': float(pos.sl) if pos.sl else None,
                'tp': float(pos.tp) if pos.tp else None,
                'profit': float(pos.profit) if pos.profit else 0
            } for pos in positions]

        except Exception as e:
            logger.error(f"Error getting open positions: {e}")
            return []