from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import MenuItem, Category
from accounts.models import Canteen
from orders.models import Order
from django.db.models import Sum

from django.utils import timezone


def menu_list(request, canteen_id):
    canteen = get_object_or_404(Canteen, id=canteen_id, is_active=True)
    categories = Category.objects.filter(items__canteen=canteen).distinct()
    selected_cat = request.GET.get('category', '')
    items = MenuItem.objects.filter(canteen=canteen, is_available=True)
    if selected_cat:
        items = items.filter(category__id=selected_cat)
    context = {
        'canteen': canteen,
        'items': items,
        'categories': categories,
        'selected_cat': selected_cat,
    }
    return render(request, 'menu/list.html', context)


def menu_detail(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id, is_available=True)
    related = MenuItem.objects.filter(canteen=item.canteen, is_available=True).exclude(id=item_id)[:4]
    return render(request, 'menu/detail.html', {'item': item, 'related': related})


# ========== VENDOR VIEWS ==========

@login_required
def vendor_dashboard(request):
    if not request.user.is_vendor():
        return redirect('dashboard')
    try:
        canteen = request.user.canteen
    except Canteen.DoesNotExist:
        messages.warning(request, 'Kamu belum punya kantin. Hubungi Admin.')
        return redirect('dashboard')

    today = timezone.now().date()
    orders_today = Order.objects.filter(canteen=canteen, created_at__date=today)
    pending = orders_today.filter(status='pending')
    processing = orders_today.filter(status='processing')
    done_today = orders_today.filter(status='done')
    revenue_today = done_today.aggregate(total=Sum('total_price'))['total'] or 0

    # Chart data: orders per hour today
    hours = list(range(6, 22))
    hourly_counts = []
    for h in hours:
        count = orders_today.filter(created_at__hour=h).count()
        hourly_counts.append(count)

    context = {
        'canteen': canteen,
        'pending_count': pending.count(),
        'processing_count': processing.count(),
        'done_count': done_today.count(),
        'revenue_today': revenue_today,
        'recent_orders': Order.objects.filter(canteen=canteen).order_by('-created_at')[:8],
        'hours_labels': json.dumps([f'{h}:00' for h in hours]),
        'hourly_counts': json.dumps(hourly_counts),
    }
    return render(request, 'vendor/dashboard.html', context)


@login_required
def vendor_menu(request):
    if not request.user.is_vendor():
        return redirect('dashboard')
    canteen = get_object_or_404(Canteen, vendor=request.user)
    items = MenuItem.objects.filter(canteen=canteen)
    categories = Category.objects.all()
    return render(request, 'vendor/menu.html', {'items': items, 'canteen': canteen, 'categories': categories})


@login_required
def vendor_menu_add(request):
    if not request.user.is_vendor():
        return redirect('dashboard')
    canteen = get_object_or_404(Canteen, vendor=request.user)
    from .forms import MenuItemForm
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.canteen = canteen
            item.save()
            messages.success(request, f'Menu "{item.name}" berhasil ditambahkan!')
            return redirect('vendor_menu')
    else:
        form = MenuItemForm()
    return render(request, 'vendor/menu_form.html', {'form': form, 'action': 'Tambah'})


@login_required
def vendor_menu_edit(request, item_id):
    if not request.user.is_vendor():
        return redirect('dashboard')
    canteen = get_object_or_404(Canteen, vendor=request.user)
    item = get_object_or_404(MenuItem, id=item_id, canteen=canteen)
    from .forms import MenuItemForm
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f'Menu "{item.name}" berhasil diperbarui!')
            return redirect('vendor_menu')
    else:
        form = MenuItemForm(instance=item)
    return render(request, 'vendor/menu_form.html', {'form': form, 'action': 'Edit', 'item': item})


@login_required
def vendor_menu_delete(request, item_id):
    if not request.user.is_vendor():
        return redirect('dashboard')
    canteen = get_object_or_404(Canteen, vendor=request.user)
    item = get_object_or_404(MenuItem, id=item_id, canteen=canteen)
    item.delete()
    messages.success(request, f'Menu "{item.name}" berhasil dihapus.')
    return redirect('vendor_menu')


@login_required
def vendor_toggle_item(request, item_id):
    if not request.user.is_vendor():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    canteen = get_object_or_404(Canteen, vendor=request.user)
    item = get_object_or_404(MenuItem, id=item_id, canteen=canteen)
    item.is_available = not item.is_available
    item.save()
    return JsonResponse({'status': 'ok', 'is_available': item.is_available})


@login_required
def vendor_orders(request):
    if not request.user.is_vendor():
        return redirect('dashboard')
    canteen = get_object_or_404(Canteen, vendor=request.user)
    status_filter = request.GET.get('status', '')
    orders = Order.objects.filter(canteen=canteen).order_by('-created_at')
    if status_filter:
        orders = orders.filter(status=status_filter)
    return render(request, 'vendor/orders.html', {'orders': orders, 'canteen': canteen, 'status_filter': status_filter})


@login_required
def vendor_order_detail(request, order_id):
    if not request.user.is_vendor():
        return redirect('dashboard')
    canteen = get_object_or_404(Canteen, vendor=request.user)
    order = get_object_or_404(Order, id=order_id, canteen=canteen)
    return render(request, 'vendor/order_detail.html', {'order': order, 'canteen': canteen})


@login_required
def vendor_update_order_status(request, order_id):
    if not request.user.is_vendor():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    canteen = get_object_or_404(Canteen, vendor=request.user)
    order = get_object_or_404(Order, id=order_id, canteen=canteen)
    new_status = request.POST.get('status')
    if new_status in ['pending', 'processing', 'done', 'cancelled']:
        order.status = new_status
        order.save()
        # Create notification for customer
        from notifications.models import Notification
        status_labels = {
            'processing': 'sedang diproses 👨‍🍳',
            'done': 'sudah siap! Silakan ambil 🎉',
            'cancelled': 'dibatalkan ❌',
        }
        if new_status in status_labels:
            Notification.objects.create(
                user=order.user,
                title='Update Pesanan',
                message=f'Pesanan #{order.queue_number} kamu {status_labels[new_status]}',
                order=order,
            )
        messages.success(request, f'Status pesanan #{order.queue_number} diperbarui ke {new_status}.')
    return redirect('vendor_order_detail', order_id=order_id)


@login_required
def vendor_stats(request):
    if not request.user.is_vendor():
        return redirect('dashboard')
    canteen = get_object_or_404(Canteen, vendor=request.user)
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    daily_revenue = []
    daily_labels = []
    for i in range(7):
        day = week_ago + timedelta(days=i)
        rev = Order.objects.filter(
            canteen=canteen,
            status='done',
            created_at__date=day
        ).aggregate(total=Sum('total_price'))['total'] or 0
        daily_revenue.append(float(rev))
        daily_labels.append(day.strftime('%d %b'))

    top_items = MenuItem.objects.filter(canteen=canteen).order_by('-order_count')[:5]

    context = {
        'canteen': canteen,
        'daily_revenue': json.dumps(daily_revenue),
        'daily_labels': json.dumps(daily_labels),
        'top_items': top_items,
        'total_revenue': Order.objects.filter(canteen=canteen, status='done').aggregate(total=Sum('total_price'))['total'] or 0,
        'total_orders': Order.objects.filter(canteen=canteen).count(),
    }
    return render(request, 'vendor/stats.html', context)
