from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Siswa / Pelanggan'),
        ('vendor', 'Penjual / Admin Kantin'),
        ('sysadmin', 'Admin Sistem'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_active = models.BooleanField(default=False)  # Nonaktif sampai admin konfirmasi
    is_approved = models.BooleanField(default=False)  # Status konfirmasi oleh admin
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def is_student(self):
        return self.role == 'student'

    def is_vendor(self):
        return self.role == 'vendor'

    def is_sysadmin(self):
        return self.role == 'sysadmin'


class Canteen(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200)
    vendor = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='canteen',
        limit_choices_to={'role': 'vendor'}
    )
    image = models.ImageField(upload_to='canteens/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    open_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Kantin'
        verbose_name_plural = 'Daftar Kantin'
