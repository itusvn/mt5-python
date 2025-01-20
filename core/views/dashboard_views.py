# core/views/dashboard_views.py

from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from models import Trade, Symbol, TradingStrategy, TradingAccount
from services.mt5_handler import MT5Handler
from services.market_data import MarketDataManager
from django.utils import timezone
from datetime import timedelta

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get account info
        mt5 = MT5Handler()
        account_info = mt5.get_account_info()
        
        # Get current positions
        positions = Trade.objects.filter(status='OPEN')
        
        # Get today's trades
        today = timezone.now().date()
        today_trades = Trade.objects.filter(
            open_time__date=today
        )

        # Calculate daily P/L
        daily_pl = sum(t.total_profit for t in today_trades if t.total_profit)
        
        context.update({
            'account_info': account_info,
            'open_positions': positions,
            'daily_pl': daily_pl,
            'total_trades': today_trades.count(),
            'winning_trades': today_trades.filter(profit__gt=0).count()
        })
        return context

class TradeListView(LoginRequiredMixin, ListView):
    model = Trade
    template_name = 'core/trade_list.html'
    context_object_name = 'trades'
    paginate_by = 50

    def get_queryset(self):
        queryset = Trade.objects.all()
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        # Filter by symbol
        symbol = self.request.GET.get('symbol')
        if symbol:
            queryset = queryset.filter(symbol__name=symbol)
            
        # Filter by date range
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(open_time__gte=date_from)
            
        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(open_time__lte=date_to)
            
        return queryset.select_related('symbol')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['symbols'] = Symbol.objects.all()
        return context

class TradeDetailView(LoginRequiredMixin, DetailView):
    model = Trade
    template_name = 'core/trade_detail.html'
    context_object_name = 'trade'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trade = self.get_object()
        
        # Get market data for chart
        market_data = MarketDataManager()
        data = market_data.get_historical_data(
            symbol=trade.symbol.name,
            timeframe='M5',
            start_date=trade.open_time - timedelta(hours=2),
            end_date=trade.close_time + timedelta(hours=2) if trade.close_time else None,
            include_indicators=True
        )
        
        context['chart_data'] = data.to_json(orient='records') if data is not None else None
        return context

class SymbolListView(LoginRequiredMixin, ListView):
    model = Symbol
    template_name = 'core/symbol_list.html'
    context_object_name = 'symbols'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get live prices for all symbols
        market_data = MarketDataManager()
        symbols_data = {}
        
        for symbol in context['symbols']:
            data = market_data.get_real_time_data(symbol.name)
            if data:
                symbols_data[symbol.name] = data
                
        context['symbols_data'] = symbols_data
        return context

class StrategyListView(LoginRequiredMixin, ListView):
    model = TradingStrategy
    template_name = 'core/strategy_list.html'
    context_object_name = 'strategies'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate performance for each strategy
        for strategy in context['strategies']:
            trades = Trade.objects.filter(strategy=strategy)
            strategy.total_trades = trades.count()
            strategy.winning_trades = trades.filter(profit__gt=0).count()
            strategy.total_profit = sum(t.total_profit for t in trades if t.total_profit)
            
        return context

# AJAX Views
def update_account_info(request):
    """Update account information via AJAX"""
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        mt5 = MT5Handler()
        account_info = mt5.get_account_info()
        
        if account_info:
            # Update account in database
            account = get_object_or_404(TradingAccount, 
                                      account_number=account_info['login'])
            account.update_metrics(account_info)
            
            return JsonResponse({
                'balance': account_info['balance'],
                'equity': account_info['equity'],
                'margin_level': account_info['margin_level'],
                'profit': account_info['profit']
            })
            
    return JsonResponse({'error': 'Invalid request'}, status=400)

def update_positions(request):
    """Update open positions via AJAX"""
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        positions = Trade.objects.filter(status='OPEN')
        
        return JsonResponse({
            'positions': [{
                'id': pos.id,
                'ticket': pos.ticket,
                'symbol': pos.symbol.name,
                'type': pos.trade_type,
                'volume': float(pos.volume),
                'open_price': float(pos.open_price),
                'current_price': float(pos.current_price) if pos.current_price else None,
                'sl': float(pos.sl) if pos.sl else None,
                'tp': float(pos.tp) if pos.tp else None,
                'profit': float(pos.profit) if pos.profit else 0,
                'swap': float(pos.swap) if pos.swap else 0,
                'total_profit': float(pos.total_profit) if pos.total_profit else 0
            } for pos in positions]
        })
        
    return JsonResponse({'error': 'Invalid request'}, status=400)