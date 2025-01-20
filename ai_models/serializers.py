# models/serializers.py

from rest_framework import serializers
from .models import AIModel, ModelPerformance, ModelPrediction

class ModelPerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelPerformance
        fields = ['date', 'accuracy', 'precision', 'recall', 'f1_score', 'profit']

class ModelPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelPrediction
        fields = ['timestamp', 'symbol', 'prediction', 'actual', 'accuracy']

class AIModelSerializer(serializers.ModelSerializer):
    performance = ModelPerformanceSerializer(many=True, read_only=True)
    recent_predictions = ModelPredictionSerializer(many=True, read_only=True)
    
    class Meta:
        model = AIModel
        fields = [
            'id', 
            'name',
            'model_type',
            'symbol',
            'description',
            'parameters',
            'created_date',
            'last_trained',
            'active',
            'version',
            'file_path',
            'performance_metrics',
            'performance',
            'recent_predictions'
        ]
        read_only_fields = ['created_date', 'last_trained']

    def to_representation(self, instance):
        """Custom representation with additional data"""
        data = super().to_representation(instance)
        
        # Add overall performance metrics
        data['overall_performance'] = {
            'accuracy': instance.get_overall_accuracy(),
            'profit': instance.get_total_profit(),
            'trades': instance.get_total_trades()
        }
        
        # Add recent performance trend
        data['performance_trend'] = instance.get_performance_trend()
        
        return data