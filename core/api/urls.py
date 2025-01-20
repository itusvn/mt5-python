from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'symbols', SymbolViewSet)
router.register(r'trades', TradeViewSet)
router.register(r'accounts', AccountViewSet)
router.register(r'strategies', StrategyViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('market-data/', include([
        path('history/', MarketDataView.as_view({'get': 'historical_data'})),
        path('live/', MarketDataView.as_view({'get': 'live_price'})),
        path('depth/', MarketDataView.as_view({'get': 'market_depth'})),
    ])),
]