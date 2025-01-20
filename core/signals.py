# core/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Trade

@receiver(post_save, sender=Trade)
def update_strategy_stats(sender, instance, created, **kwargs):
    if instance.strategy:
        instance.strategy.update_stats()