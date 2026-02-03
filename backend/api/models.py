from django.db import models
from django.contrib.auth.models import User

class EquipmentDataset(models.Model):
    # Link every upload to a specific user
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_name = models.CharField(max_length=255)
    total_records = models.IntegerField(default=0)
    summary_stats = models.JSONField(default=dict) 

    def __str__(self):
        return f"{self.file_name} - {self.uploaded_at} ({self.user.username if self.user else 'Anon'})"