import qrcode
import io
import base64
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from accounts.models import Canteen
from django.conf import settings
import os


def generate_qr_image(data, size=10):
    """Generate QR code and return as base64 string"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=size,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#0F1117', back_color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


@login_required
def scan_qr(request):
    """QR scanner page for students"""
    if not request.user.is_student():
        return redirect('dashboard')
    # Pass active canteen session to template
    from accounts.models import Canteen
    active_canteen = None
    canteen_id = request.session.get('selected_canteen_id')
    if canteen_id:
        try:
            active_canteen = Canteen.objects.get(id=canteen_id)
        except Canteen.DoesNotExist:
            del request.session['selected_canteen_id']
    return render(request, 'qrcode_app/scan.html', {'active_canteen': active_canteen})


@login_required
def process_qr(request):
    """Process scanned QR data — set canteen session and redirect to menu"""
    if not request.user.is_student():
        return redirect('dashboard')
    canteen_id = request.GET.get('canteen_id')
    if canteen_id:
        try:
            canteen = Canteen.objects.get(id=canteen_id, is_active=True)
            # Save canteen to session so student can order from it
            request.session['selected_canteen_id'] = canteen.id
            request.session['selected_canteen_name'] = canteen.name
            # Clear cart if switching to different canteen
            from orders.models import Cart
            try:
                cart = request.user.cart
                if cart.canteen and cart.canteen.id != canteen.id:
                    cart.cart_items.all().delete()
                    cart.canteen = None
                    cart.save()
                    messages.warning(request, f'Keranjang direset karena kamu pindah ke {canteen.name}.')
            except Exception:
                pass
            messages.success(request, f'QR berhasil dipindai! Kamu sekarang bisa memesan dari "{canteen.name}".')
            return redirect('student_menu')
        except Canteen.DoesNotExist:
            messages.error(request, 'Kantin tidak ditemukan atau sedang tidak aktif.')
    else:
        messages.error(request, 'QR Code tidak valid. Pastikan QR berasal dari kantin SmartFood.')
    return redirect('scan_qr')


@login_required
def clear_canteen_session(request):
    """Allow student to clear canteen session (change canteen)"""
    if not request.user.is_student():
        return redirect('dashboard')
    request.session.pop('selected_canteen_id', None)
    request.session.pop('selected_canteen_name', None)
    messages.info(request, 'Sesi kantin dihapus. Silakan scan QR kantin baru.')
    return redirect('scan_qr')


@login_required
def choose_canteen(request):
    """Manual canteen selection page - fallback when QR doesn't match"""
    if not request.user.is_student():
        return redirect('dashboard')
    from accounts.models import Canteen
    canteens = Canteen.objects.filter(is_active=True)
    return render(request, 'qrcode_app/choose_canteen.html', {'canteens': canteens})


@login_required
def vendor_qr(request):
    """Generate QR for vendor's canteen"""
    if not request.user.is_vendor():
        return redirect('dashboard')
    canteen = get_object_or_404(Canteen, vendor=request.user)

    # Build the QR data URL
    base_url = request.build_absolute_uri(f'/menu/{canteen.id}/')
    qr_data = f'{base_url}'
    qr_b64 = generate_qr_image(qr_data)

    context = {
        'canteen': canteen,
        'qr_b64': qr_b64,
        'qr_url': qr_data,
    }
    return render(request, 'vendor/qr.html', context)


@login_required
def download_qr(request):
    """Download QR code as PNG image"""
    if not request.user.is_vendor():
        return redirect('dashboard')
    canteen = get_object_or_404(Canteen, vendor=request.user)
    base_url = request.build_absolute_uri(f'/menu/{canteen.id}/')
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=15, border=4)
    qr.add_data(base_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#0F1117', back_color='white')
    response = HttpResponse(content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="qr_{canteen.name}.png"'
    img.save(response, 'PNG')
    return response
