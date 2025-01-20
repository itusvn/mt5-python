# trading/api/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from ..models import Order, TradingStrategy
from ..services.execution_service import ExecutionService
from ..services.strategy_service import StrategyService
from .serializers import OrderSerializer, StrategySerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    execution_service = ExecutionService()

    @action(detail=False, methods=['post'])
    def place_order(self, request):
        """Place new trading order"""
        try:
            result = self.execution_service.execute_order(
                symbol=request.data['symbol'],
                position_type=request.data['position_type'],
                volume=request.data['volume'],
                selected_models=request.data.get('selected_models', []),
                sl=request.data.get('stop_loss'),
                tp=request.data.get('take_profit')
            )

            if result['success']:
                order = Order.objects.get(id=result['order_id'])
                return Response(
                    OrderSerializer(order).data,
                    status=status.HTTP_201_CREATED
                )

            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def close_order(self, request, pk=None):
        """Close existing order"""
        try:
            result = self.execution_service.close_order(order_id=pk)

            if result['success']:
                order = Order.objects.get(id=pk)
                return Response(OrderSerializer(order).data)

            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def modify_order(self, request, pk=None):
        """Modify order SL/TP"""
        try:
            result = self.execution_service.modify_order(
                order_id=pk,
                sl=request.data.get('stop_loss'),
                tp=request.data.get('take_profit')
            )

            if result['success']:
                order = Order.objects.get(id=pk)
                return Response(OrderSerializer(order).data)

            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class StrategyViewSet(viewsets.ModelViewSet):
    queryset = TradingStrategy.objects.all()
    serializer_class = StrategySerializer
    permission_classes = [IsAuthenticated]
    strategy_service = StrategyService()

    def create(self, request):
        """Create new trading strategy"""
        try:
            strategy = self.strategy_service.create_strategy(
                name=request.data['name'],
                symbol=request.data['symbol'],
                timeframe=request.data['timeframe'],
                parameters=request.data['parameters'],
                risk_settings=request.data['risk_settings'],
                selected_models=request.data['selected_models'],
                model_weights=request.data.get('model_weights')
            )

            return Response(
                StrategySerializer(strategy).data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def get_signals(self, request, pk=None):
        """Get current trading signals for strategy"""
        try:
            strategy = self.get_object()
            signals = self.strategy_service.get_strategy_signals(strategy)

            return Response(signals)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """Get strategy performance statistics"""
        try:
            strategy = self.get_object()
            days = int(request.query_params.get('days', 30))
            stats = self.strategy_service.get_strategy_stats(
                strategy=strategy,
                days=days
            )

            return Response(stats)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def optimize(self, request, pk=None):
        """Optimize strategy parameters"""
        try:
            strategy = self.get_object()
            result = self.strategy_service.optimize_strategy(
                strategy=strategy,
                parameter_ranges=request.data['parameter_ranges'],
                optimization_target=request.data.get('optimization_target', 'sharpe_ratio')
            )

            return Response(result)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )