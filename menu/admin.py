from django.contrib import admin
from .models import MenuItem, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon']

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'canteen', 'price', 'is_available', 'order_count']
    list_filter = ['is_available', 'canteen']
    search_fields = ['name']
