# models/models.py

from datetime import timezone
from django.db import models
import jsonfield

class AIModel(models.Model):
    MODEL_TYPES = [
        ('price_predictor', 'Price Predictor'),
        ('trend_classifier', 'Trend Classifier'),
        ('rl_agent', 'Reinforcement Learning Agent')
    ]

    name = models.CharField(max_length=100)
    model_type = models.CharField(max_length=20, choices=MODEL_TYPES)
    symbol = models.CharField(max_length=10)
    description = models.TextField(blank=True)
    parameters = jsonfield.JSONField(default=dict)
    
    # Tracking fields
    created_date = models.DateTimeField(auto_now_add=True)
    last_trained = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=False)
    version = models.CharField(max_length=10)
    file_path = models.CharField(max_length=255)
    
    # Performance metrics
    performance_metrics = jsonfield.JSONField(default=dict)

    class Meta:
        ordering = ['-last_trained']

    def __str__(self):
        return f"{self.name} ({self.symbol})"

    def get_overall_accuracy(self):
        """Calculate overall accuracy from performance history"""
        performances = self.performance.all()
        if not performances:
            return 0
        return sum(p.accuracy for p in performances) / len(performances)

    def get_total_profit(self):
        """Calculate total profit from all predictions"""
        performances = self.performance.all()
        return sum(p.profit for p in performances if p.profit)

    def get_total_trades(self):
        """Get total number of trades"""
        return self.predictions.count()

    def get_performance_trend(self, days=30):
        """Get performance trend for last n days"""
        return self.performance.filter(
            date__gte=timezone.now() - timezone.timedelta(days=days)
        ).values('date', 'accuracy', 'profit')

class ModelPerformance(models.Model):
    """Track model performance metrics over time"""
    model = models.ForeignKey(
        AIModel, 
        related_name='performance',
        on_delete=models.CASCADE
    )
    date = models.DateTimeField(auto_now_add=True)
    accuracy = models.FloatField()
    precision = models.FloatField()
    recall = models.FloatField()
    f1_score = models.FloatField()
    profit = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['-date']

class ModelPrediction(models.Model):
    """Track individual predictions and their outcomes"""
    model = models.ForeignKey(
        AIModel,
        related_name='predictions',
        on_delete=models.CASCADE
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    symbol = models.CharField(max_length=10)
    prediction = models.CharField(max_length=20)
    actual = models.CharField(max_length=20, null=True, blank=True)
    accuracy = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

class ModelTrainingLog(models.Model):
    """Track model training history"""
    model = models.ForeignKey(
        AIModel,
        related_name='training_logs',
        on_delete=models.CASCADE
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    duration = models.IntegerField()  # in seconds
    epochs = models.IntegerField()
    loss = models.FloatField()
    val_loss = models.FloatField()
    status = models.CharField(max_length=20)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']