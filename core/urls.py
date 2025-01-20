# core/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import views as api_views
from .views import dashboard_views

# API Router
router = DefaultRouter()
router.register(r'symbols', api_views.SymbolViewSet)
router.register(r'trades', api_views.TradeViewSet)
router.register(r'accounts', api_views.AccountViewSet)
router.register(r'strategies', api_views.StrategyViewSet)

app_name = 'core'

urlpatterns = [
    # API URLs
    path('api/', include([
        path('', include(router.urls)),
        path('market-data/', include([
            path('history/', api_views.MarketDataView.as_view({'get': 'historical_data'})),
            path('live/', api_views.MarketDataView.as_view({'get': 'live_price'})),
            path('depth/', api_views.MarketDataView.as_view({'get': 'market_depth'})),
        ])),
    ])),
    
    # Dashboard URLs
    path('', dashboard_views.DashboardView.as_view(), name='dashboard'),
    path('trades/', dashboard_views.TradeListView.as_view(), name='trade-list'),
    path('trades/<int:pk>/', dashboard_views.TradeDetailView.as_view(), name='trade-detail'),
    path('symbols/', dashboard_views.SymbolListView.as_view(), name='symbol-list'),
    path('strategies/', dashboard_views.StrategyListView.as_view(), name='strategy-list'),
    
    # AJAX endpoints
    path('ajax/', include([
        path('update-account/', dashboard_views.update_account_info, name='update-account'),
        path('update-positions/', dashboard_views.update_positions, name='update-positions'),
    ])),
]