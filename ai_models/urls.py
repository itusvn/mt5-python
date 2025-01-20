# urls.py

from django.urls import path
from .views import ModelManagementView

urlpatterns = [
    # Other URLs...
    path('models/management/', ModelManagementView.as_view(), name='model_management'),
]