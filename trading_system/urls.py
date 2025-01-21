# urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Main Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # Trading Views
    path('trading/', views.TradingView.as_view(), name='trading'),
    path('trading/chart/', views.ChartView.as_view(), name='chart'),
    
    # Account & Orders
    path('account/', views.AccountView.as_view(), name='account'),
    path('orders/', views.OrderListView.as_view(), name='orders'),
    
    # AI Models
    path('models/', views.ModelListView.as_view(), name='models'),
    path('models/<int:pk>/', views.ModelDetailView.as_view(), name='model_detail'),
    
    # WebSocket URLs
    path('ws/prices/', consumers.PriceConsumer.as_asgi()),
    path('ws/trades/', consumers.TradeConsumer.as_asgi()),
]