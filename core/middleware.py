# core/middleware.py
from django.core.exceptions import PermissionDenied

class TradePermissionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check permissions here
        return self.get_response(request)