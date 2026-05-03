from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['queue_number', 'user', 'canteen', 'status', 'total_price', 'created_at']
    list_filter = ['status', 'canteen']
    search_fields = ['user__username']

admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(OrderItem)
