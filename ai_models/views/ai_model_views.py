# views/model_views.py

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from ai_models import AIModel
from serializers import AIModelSerializer
from services.ai_model_service import ModelService

class AIModelViewSet(viewsets.ModelViewSet):
    queryset = AIModel.objects.all()
    serializer_class = AIModelSerializer
    
    @action(detail=False, methods=['post'])
    def train(self, request):
        """Train new model"""
        try:
            model_service = ModelService()
            result = model_service.train_model(
                model_type=request.data['model_type'],
                symbol=request.data['symbol'],
                training_days=int(request.data['training_days'])
            )
            return Response(result)
        except Exception as e:
            return Response({'status': 'error', 'error': str(e)})
    
    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """Get model details and performance"""
        model = self.get_object()
        model_service = ModelService()
        details = model_service.get_model_details(model)
        return Response(details)
    
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """Toggle model active status"""
        model = self.get_object()
        model.active = not model.active
        model.save()
        return Response({'status': 'success'})