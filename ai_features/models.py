from django.db import models
from accounts.models import CustomUser


class AnomalyLog(models.Model):
    SEVERITY_CHOICES = [
        ('low', 'Rendah'),
        ('medium', 'Sedang'),
        ('high', 'Tinggi'),
    ]
    EVENT_CHOICES = [
        ('spam_order', 'Spam Pesanan'),
        ('mass_cancel', 'Banyak Batalkan'),
        ('unusual_activity', 'Aktivitas Mencurigakan'),
        ('bulk_order', 'Pesanan Massal'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='anomaly_logs')
    event_type = models.CharField(max_length=50, choices=EVENT_CHOICES)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    detected_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"[{self.severity.upper()}] {self.user.username} - {self.event_type}"

    class Meta:
        ordering = ['-detected_at']
        verbose_name = 'Log Anomali'
        verbose_name_plural = 'Log Anomali'
