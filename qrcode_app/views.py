import qrcode
import io
import base64
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
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
    return render(request, 'qrcode_app/scan.html')


@login_required
def process_qr(request):
    """Process scanned QR data and redirect to menu"""
    canteen_id = request.GET.get('canteen_id')
    if canteen_id:
        canteen = get_object_or_404(Canteen, id=canteen_id, is_active=True)
        return redirect('menu_list', canteen_id=canteen.id)
    return redirect('landing')


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
