from django.db import models
from accounts.models import CustomUser, Canteen
from menu.models import MenuItem


class Cart(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='cart')
    canteen = models.ForeignKey(Canteen, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Keranjang - {self.user.username}"

    def total_price(self):
        return sum(item.subtotal() for item in self.cart_items.all())

    def total_items(self):
        return sum(item.quantity for item in self.cart_items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cart_items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.menu_item.price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Menunggu'),
        ('processing', 'Diproses'),
        ('done', 'Selesai'),
        ('cancelled', 'Dibatalkan'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders')
    canteen = models.ForeignKey(Canteen, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    queue_number = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.queue_number} - {self.user.username}"

    def get_queue_position(self):
        """Returns queue position (how many ahead in line)"""
        ahead = Order.objects.filter(
            canteen=self.canteen,
            status__in=['pending', 'processing'],
            created_at__lt=self.created_at
        ).count()
        return ahead

    class Meta:
        ordering = ['-created_at']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=0)

    def save(self, *args, **kwargs):
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"


def generate_queue_number(canteen):
    """Generate next queue number for a canteen (resets daily)"""
    from django.utils import timezone
    today = timezone.now().date()
    last_order = Order.objects.filter(
        canteen=canteen,
        created_at__date=today
    ).order_by('-queue_number').first()
    if last_order:
        return last_order.queue_number + 1
    return 1
