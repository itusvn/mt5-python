# views/model_management_views.py

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from models import AIModel

class ModelManagementView(LoginRequiredMixin, TemplateView):
    template_name = 'models/model_management.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all models and their information
        models = AIModel.objects.all().prefetch_related(
            'performance',
            'predictions'
        )
        context['models'] = models
        return context