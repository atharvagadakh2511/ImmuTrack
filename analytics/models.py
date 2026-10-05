from django.db import models
from children.models import Child

class DefaulterRiskLevel(models.TextChoices):
    LOW = 'LOW', 'Low Risk'
    MEDIUM = 'MEDIUM', 'Moderate Risk'
    HIGH = 'HIGH', 'High Defaulter Risk'
    INSUFFICIENT_DATA = 'INSUFFICIENT_DATA', 'Insufficient Data'

class MLModelMetadata(models.Model):
    model_name = models.CharField(max_length=100)
    version = models.CharField(max_length=50)
    trained_at = models.DateTimeField(auto_now_add=True)
    accuracy = models.FloatField()
    precision = models.FloatField()
    recall = models.FloatField()
    f1_score = models.FloatField()
    features_used = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.model_name} v{self.version} (F1: {self.f1_score:.2f})"

class ChildRiskAssessment(models.Model):
    child = models.OneToOneField(Child, on_delete=models.CASCADE, related_name='risk_assessment')
    model_version = models.ForeignKey(MLModelMetadata, on_delete=models.SET_NULL, null=True, blank=True)
    risk_level = models.CharField(max_length=30, choices=DefaulterRiskLevel.choices, default=DefaulterRiskLevel.INSUFFICIENT_DATA)
    probability = models.FloatField(default=0.0)
    top_risk_factor = models.CharField(max_length=255, default='Standard Monitoring')
    assessed_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.child.full_name}: {self.risk_level} ({self.probability:.2f})"
