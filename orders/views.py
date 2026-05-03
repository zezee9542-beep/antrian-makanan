from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Cart, CartItem, Order, OrderItem, generate_queue_number
from menu.models import MenuItem
from accounts.models import Canteen
import json


# =========== CART VIEWS ===========

@login_required
def cart_view(request):
    if not request.user.is_student():
        return redirect('dashboard')
    cart, _ = Cart.objects.get_or_create(user=request.user)
    return render(request, 'orders/cart.html', {'cart': cart})


@login_required
def add_to_cart(request, item_id):
    if not request.user.is_student():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    item = get_object_or_404(MenuItem, id=item_id, is_available=True)
    cart, _ = Cart.objects.get_or_create(user=request.user)

    # If cart has items from different canteen, clear it
    if cart.canteen and cart.canteen != item.canteen:
        cart.cart_items.all().delete()
        cart.canteen = item.canteen
        cart.save()
        messages.warning(request, 'Keranjang direset karena beda kantin.')

    cart.canteen = item.canteen
    cart.save()

    cart_item, created = CartItem.objects.get_or_create(cart=cart, menu_item=item)
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'ok',
            'total_items': cart.total_items(),
            'total_price': str(cart.total_price()),
        })
    messages.success(request, f'{item.name} ditambahkan ke keranjang!')
    return redirect(request.META.get('HTTP_REFERER', 'menu_list'))


@login_required
def remove_from_cart(request, item_id):
    if not request.user.is_student():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    cart = get_object_or_404(Cart, user=request.user)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    cart_item.delete()
    if cart.total_items() == 0:
        cart.canteen = None
        cart.save()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'total_items': cart.total_items(), 'total_price': str(cart.total_price())})
    return redirect('cart')


@login_required
def update_cart_quantity(request, item_id):
    if not request.user.is_student():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    cart = get_object_or_404(Cart, user=request.user)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    qty = int(request.POST.get('quantity', 1))
    if qty <= 0:
        cart_item.delete()
    else:
        cart_item.quantity = qty
        cart_item.save()
    return JsonResponse({'status': 'ok', 'total_items': cart.total_items(), 'total_price': str(cart.total_price())})


@login_required
def checkout(request):
    if not request.user.is_student():
        return redirect('dashboard')
    cart = get_object_or_404(Cart, user=request.user)
    if cart.total_items() == 0:
        messages.error(request, 'Keranjang kamu kosong!')
        return redirect('cart')

    notes = request.POST.get('notes', '')
    canteen = cart.canteen

    # Anomaly detection: check for spam orders
    from django.utils import timezone
    recent_orders = Order.objects.filter(
        user=request.user,
        created_at__gte=timezone.now() - timezone.timedelta(minutes=2)
    ).count()
    if recent_orders >= 5:
        from ai_features.models import AnomalyLog
        AnomalyLog.objects.create(
            user=request.user,
            event_type='spam_order',
            description=f'User melakukan {recent_orders} pesanan dalam 2 menit',
            severity='high'
        )
        messages.error(request, 'Terlalu banyak pesanan. Coba beberapa saat lagi.')
        return redirect('cart')

    queue_number = generate_queue_number(canteen)
    total = cart.total_price()

    order = Order.objects.create(
        user=request.user,
        canteen=canteen,
        queue_number=queue_number,
        total_price=total,
        notes=notes,
        status='pending',
    )

    for ci in cart.cart_items.all():
        OrderItem.objects.create(
            order=order,
            menu_item=ci.menu_item,
            quantity=ci.quantity,
            unit_price=ci.menu_item.price,
            subtotal=ci.subtotal(),
        )
        ci.menu_item.order_count += ci.quantity
        ci.menu_item.save()

    cart.cart_items.all().delete()
    cart.canteen = None
    cart.save()

    from notifications.models import Notification
    Notification.objects.create(
        user=request.user,
        title='Pesanan Diterima! 🎉',
        message=f'Pesanan #{queue_number} kamu di {canteen.name} berhasil dibuat. Nomor antrian: {queue_number}',
        order=order,
    )

    messages.success(request, f'Pesanan berhasil! Nomor antrian kamu: #{queue_number}')
    return redirect('queue_status', order_id=order.id)


# =========== ORDER VIEWS ===========

@login_required
def order_history(request):
    if not request.user.is_student():
        return redirect('dashboard')
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/history.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    if not request.user.is_student():
        return redirect('dashboard')
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/detail.html', {'order': order})


# =========== QUEUE VIEWS ===========

@login_required
def queue_status(request, order_id):
    if not request.user.is_student():
        return redirect('dashboard')
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/queue_status.html', {'order': order})


@login_required
def queue_status_api(request, order_id):
    """AJAX endpoint for real-time queue polling"""
    if not request.user.is_student():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    order = get_object_or_404(Order, id=order_id, user=request.user)
    position = order.get_queue_position()
    estimated_minutes = position * 5  # avg 5 min per order

    return JsonResponse({
        'status': order.status,
        'status_display': order.get_status_display(),
        'queue_number': order.queue_number,
        'position': position,
        'estimated_minutes': estimated_minutes,
        'canteen_name': order.canteen.name,
    })
