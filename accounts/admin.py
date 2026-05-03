from django.contrib import admin
from .models import CustomUser, Canteen

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active']
    search_fields = ['username', 'email']

@admin.register(Canteen)
class CanteenAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor', 'location', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'location']
