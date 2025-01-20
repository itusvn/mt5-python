from symtable import Symbol
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from core.api.serializers import (
    AccountSerializer,
    OrderRequestSerializer,
    StrategySerializer,
    SymbolSerializer,
    TradeSerializer,
    ModifyOrderSerializer,
)
from core.models.account import TradingAccount
from core.models.strategy import TradingStrategy
from core.models.trade import Trade
from services.mt5_handler import MT5Handler
from services.market_data import MarketDataManager
from services.order_manager import OrderManager
from ..utils.exceptions import OrderExecutionError
import logging

logger = logging.getLogger(__name__)


class SymbolViewSet(viewsets.ModelViewSet):
    queryset = Symbol.objects.all()
    serializer_class = SymbolSerializer

    @action(detail=True, methods=["get"])
    def market_info(self, request, pk=None):
        symbol = self.get_object()
        market_data = MarketDataManager()
        info = market_data.get_symbol_info(symbol.name)

        if info:
            return Response(info)
        return Response(
            {"error": "Could not fetch market info"}, status=status.HTTP_400_BAD_REQUEST
        )


class TradeViewSet(viewsets.ModelViewSet):
    queryset = Trade.objects.all()
    serializer_class = TradeSerializer
    order_manager = OrderManager()

    @action(detail=False, methods=["post"])
    def place_order(self, request):
        serializer = OrderRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Validate order
                is_valid, error = self.order_manager.validate_order(
                    symbol=serializer.validated_data["symbol"],
                    order_type=serializer.validated_data["type"],
                    volume=serializer.validated_data["volume"],
                    sl=serializer.validated_data.get("sl"),
                    tp=serializer.validated_data.get("tp"),
                )
                if not is_valid:
                    return Response(
                        {"error": error}, status=status.HTTP_400_BAD_REQUEST
                    )

                # Check margin
                has_margin, error = self.order_manager.check_margin_requirements(
                    symbol=serializer.validated_data["symbol"],
                    volume=serializer.validated_data["volume"],
                )
                if not has_margin:
                    return Response(
                        {"error": error}, status=status.HTTP_400_BAD_REQUEST
                    )

                # Place order
                result = self.order_manager.place_market_order(
                    **serializer.validated_data
                )

                if result["success"]:
                    trade = Trade.objects.get(id=result["trade_id"])
                    return Response(TradeSerializer(trade).data)
                return Response(
                    {"error": result["error"]}, status=status.HTTP_400_BAD_REQUEST
                )

            except Exception as e:
                logger.error(f"Error placing order: {e}")
                return Response(
                    {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def close_position(self, request, pk=None):
        trade = self.get_object()
        result = self.order_manager.close_position(trade.ticket)

        if result["success"]:
            trade.refresh_from_db()
            return Response(TradeSerializer(trade).data)
        return Response({"error": result["error"]}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def modify_position(self, request, pk=None):
        trade = self.get_object()
        serializer = ModifyOrderSerializer(data=request.data)

        if serializer.is_valid():
            result = self.order_manager.modify_position(
                ticket=trade.ticket,
                sl=serializer.validated_data.get("sl"),
                tp=serializer.validated_data.get("tp"),
            )

            if result["success"]:
                trade.refresh_from_db()
                return Response(TradeSerializer(trade).data)
            return Response(
                {"error": result["error"]}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MarketDataView(viewsets.ViewSet):
    market_data = MarketDataManager()

    def historical_data(self, request):
        try:
            data = self.market_data.get_historical_data(
                symbol=request.GET.get("symbol"),
                timeframe=int(request.GET.get("timeframe")),
                start_date=request.GET.get("start_date"),
                end_date=request.GET.get("end_date"),
                include_indicators=bool(request.GET.get("indicators", False)),
            )
            if data is not None:
                return Response(data.to_dict("records"))
            return Response(
                {"error": "Could not fetch historical data"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def live_price(self, request):
        try:
            data = self.market_data.get_real_time_data(symbol=request.GET.get("symbol"))
            if data:
                return Response(data)
            return Response(
                {"error": "Could not fetch live price"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AccountViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TradingAccount.objects.filter(is_active=True)
    serializer_class = AccountSerializer

    @action(detail=True, methods=["get"])
    def metrics(self, request, pk=None):
        account = self.get_object()
        mt5 = MT5Handler()
        info = mt5.get_account_info()

        if info:
            account.update_metrics(info)
            return Response(AccountSerializer(account).data)
        return Response(
            {"error": "Could not fetch account metrics"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class StrategyViewSet(viewsets.ModelViewSet):
    queryset = TradingStrategy.objects.all()
    serializer_class = StrategySerializer

    @action(detail=True, methods=["get"])
    def performance(self, request, pk=None):
        strategy = self.get_object()
        trades = Trade.objects.filter(strategy=strategy)

        return Response(
            {
                "total_trades": trades.count(),
                "winning_trades": trades.filter(profit__gt=0).count(),
                "total_profit": sum(t.total_profit for t in trades),
                "win_rate": strategy.win_rate,
            }
        )
