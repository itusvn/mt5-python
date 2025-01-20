# core/admin.py
from django.contrib import admin
from .models import Symbol, Trade, TradingAccount, TradingStrategy

@admin.register(Symbol)
class SymbolAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'pip_value', 'spread', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'display_name']
    list_editable = ['is_active']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'display_name', 'is_active')
        }),
        ('Trading Parameters', {
            'fields': ('pip_value', 'spread', 'min_lot', 'max_lot', 'margin_required')
        })
    )

@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = [
        'ticket', 'symbol', 'trade_type', 'volume',
        'status', 'open_time', 'profit'
    ]
    list_filter = ['status', 'trade_type', 'symbol']
    search_fields = ['ticket', 'comment']
    date_hierarchy = 'open_time'
    readonly_fields = ['ticket', 'open_time', 'close_time', 'profit']
    
    fieldsets = (
        ('Trade Info', {
            'fields': ('ticket', 'symbol', 'trade_type', 'volume', 'status')
        }),
        ('Price Levels', {
            'fields': ('open_price', 'close_price', 'sl', 'tp')
        }),
        ('Time', {
            'fields': ('open_time', 'close_time')
        }),
        ('Results', {
            'fields': ('profit', 'swap', 'commission')
        }),
        ('Additional Info', {
            'fields': ('magic_number', 'comment'),
            'classes': ('collapse',)
        })
    )

    def has_add_permission(self, request):
        return False  # Trades should only be created through MT5

@admin.register(TradingAccount)
class TradingAccountAdmin(admin.ModelAdmin):
    list_display = [
        'account_number', 'broker', 'balance',
        'equity', 'margin_level', 'is_active'
    ]
    list_filter = ['is_demo', 'is_active', 'broker']
    search_fields = ['account_number']
    readonly_fields = ['balance', 'equity', 'margin', 'margin_level']
    
    fieldsets = (
        ('Account Info', {
            'fields': ('account_number', 'broker', 'currency', 'leverage')
        }),
        ('Status', {
            'fields': ('is_demo', 'is_active')
        }),
        ('Account Metrics', {
            'fields': ('balance', 'equity', 'margin', 'free_margin', 'margin_level'),
            'classes': ('collapse',)
        })
    )

@admin.register(TradingStrategy)
class TradingStrategyAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'symbol', 'timeframe',
        'total_trades', 'win_rate', 'is_active'
    ]
    list_filter = ['is_active', 'symbol', 'timeframe']
    search_fields = ['name']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Strategy Info', {
            'fields': ('name', 'description', 'symbol', 'timeframe')
        }),
        ('Risk Settings', {
            'fields': ('risk_per_trade', 'max_trades', 'is_active')
        }),
        ('Parameters', {
            'fields': ('parameters',),
            'classes': ('collapse',)
        }),
        ('Performance', {
            'fields': ('total_trades', 'winning_trades', 'total_profit'),
            'classes': ('collapse',)
        })
    )