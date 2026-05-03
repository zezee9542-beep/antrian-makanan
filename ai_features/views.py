from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from orders.models import Order, OrderItem
from menu.models import MenuItem
from accounts.models import Canteen
from .models import AnomalyLog
from django.conf import settings
from datetime import datetime, timedelta
from django.db.models import Count, Sum


def get_recommendation_logic(user):
    """
    Rule-based food recommendation engine.
    Falls back to OpenAI if API key is set.
    """
    now = timezone.localtime()
    hour = now.hour

    # Time-based context
    if 6 <= hour < 10:
        time_context = 'pagi'
        time_hint = 'Pagi ini, cocok untuk sarapan ringan.'
    elif 10 <= hour < 15:
        time_context = 'siang'
        time_hint = 'Waktu makan siang! Pilih yang mengenyangkan.'
    else:
        time_context = 'sore'
        time_hint = 'Sore hari, cocok untuk camilan atau minuman.'

    # Get user's past orders
    past_items = OrderItem.objects.filter(
        order__user=user,
        order__status='done'
    ).values('menu_item__id', 'menu_item__name', 'menu_item__canteen__id').annotate(
        count=Count('id')
    ).order_by('-count')[:5]

    # Get popular items
    popular_items = MenuItem.objects.filter(
        is_available=True
    ).order_by('-order_count')[:6]

    # Build recommendations
    recommendations = []
    seen_ids = set()

    # First: items user ordered before but not yet today
    today = timezone.now().date()
    ordered_today_ids = set(
        OrderItem.objects.filter(
            order__user=user,
            order__created_at__date=today
        ).values_list('menu_item__id', flat=True)
    )

    for past in past_items:
        item_id = past['menu_item__id']
        if item_id not in ordered_today_ids and item_id not in seen_ids:
            try:
                item = MenuItem.objects.get(id=item_id, is_available=True)
                recommendations.append({
                    'id': item.id,
                    'name': item.name,
                    'price': str(item.price),
                    'canteen': item.canteen.name,
                    'image': item.image.url if item.image else None,
                    'reason': 'Kamu sering pesan ini sebelumnya 🔄',
                    'category': 'favorite'
                })
                seen_ids.add(item_id)
            except MenuItem.DoesNotExist:
                pass

    # Then: popular items not yet recommended
    for item in popular_items:
        if item.id not in seen_ids and len(recommendations) < 5:
            recommendations.append({
                'id': item.id,
                'name': item.name,
                'price': str(item.price),
                'canteen': item.canteen.name,
                'image': item.image.url if item.image else None,
                'reason': f'Populer saat {time_context} ⭐',
                'category': 'popular'
            })
            seen_ids.add(item.id)

    return {
        'time_context': time_context,
        'time_hint': time_hint,
        'recommendations': recommendations[:5],
        'ai_powered': bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != 'your-openai-api-key-here'),
    }


def get_openai_recommendation(user, context_data):
    """Use OpenAI GPT for natural language recommendation"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        items_str = ', '.join([r['name'] for r in context_data['recommendations']])
        prompt = f"""Kamu adalah asisten rekomendasi makanan di kantin sekolah.
Waktu sekarang: {context_data['time_context']}.
Menu yang tersedia dan relevan: {items_str}.
Berikan satu kalimat rekomendasi hangat dalam Bahasa Indonesia yang personal dan menarik.
Maksimal 2 kalimat. Jangan gunakan emoji berlebihan."""

        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=100,
        )
        return response.choices[0].message.content
    except Exception:
        return context_data['time_hint']


def get_demand_prediction(canteen):
    """Predict busy hours based on historical orders"""
    now = timezone.now()
    week_ago = now - timedelta(days=7)

    hourly_data = []
    peak_hour = None
    peak_count = 0

    for h in range(6, 22):
        count = Order.objects.filter(
            canteen=canteen,
            created_at__gte=week_ago,
            created_at__hour=h,
        ).count()
        hourly_data.append({'hour': f'{h}:00', 'count': count})
        if count > peak_count:
            peak_count = count
            peak_hour = h

    suggestions = []
    if peak_hour:
        suggestions.append(f'Jam {peak_hour}:00 adalah jam paling ramai ({peak_count} pesanan/minggu).')
        suggestions.append(f'Siapkan stok ekstra 30 menit sebelum jam {peak_hour}:00.')

    avg_orders = sum(d['count'] for d in hourly_data) / max(len(hourly_data), 1)
    if avg_orders > 5:
        top_items = MenuItem.objects.filter(canteen=canteen).order_by('-order_count')[:3]
        if top_items:
            names = ', '.join([i.name for i in top_items])
            suggestions.append(f'Stok terbanyak untuk: {names}.')

    return {
        'hourly_data': hourly_data,
        'peak_hour': peak_hour,
        'peak_count': peak_count,
        'suggestions': suggestions,
    }


# ====== VIEWS ======

@login_required
def ai_recommend(request):
    """API endpoint: AI food recommendation for students"""
    if not request.user.is_student():
        return JsonResponse({'error': 'Hanya untuk siswa'}, status=403)

    context_data = get_recommendation_logic(request.user)

    # If OpenAI key is configured, get AI message
    ai_message = context_data['time_hint']
    if context_data['ai_powered'] and context_data['recommendations']:
        ai_message = get_openai_recommendation(request.user, context_data)

    return JsonResponse({
        'ai_message': ai_message,
        'recommendations': context_data['recommendations'],
        'time_context': context_data['time_context'],
        'ai_powered': context_data['ai_powered'],
    })


@login_required
def ai_predict(request):
    """API endpoint: demand prediction for vendors"""
    if not request.user.is_vendor():
        return JsonResponse({'error': 'Hanya untuk penjual'}, status=403)
    try:
        canteen = request.user.canteen
    except Exception:
        return JsonResponse({'error': 'Kantin tidak ditemukan'}, status=404)

    prediction = get_demand_prediction(canteen)
    return JsonResponse(prediction)


@login_required
def ai_anomaly_check(request):
    """API endpoint: get anomaly logs for system admin"""
    if not request.user.is_sysadmin():
        return JsonResponse({'error': 'Hanya untuk admin'}, status=403)
    logs = AnomalyLog.objects.filter(is_resolved=False).select_related('user').values(
        'id', 'user__username', 'event_type', 'description', 'severity', 'detected_at'
    )[:20]
    return JsonResponse({'anomalies': list(logs)})
