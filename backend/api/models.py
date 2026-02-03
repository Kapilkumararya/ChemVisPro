from django.db import models

class EquipmentDataset(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_name = models.CharField(max_length=255)
    total_records = models.IntegerField(default=0)
    summary_stats = models.JSONField(default=dict) 

    def __str__(self):
        return f"{self.file_name} - {self.uploaded_at}"