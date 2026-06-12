from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db import models
from django.db.models import Q, Count, Sum
from .forms import RegisterForm, LoginForm, ProfileUpdateForm
from .models import CustomUser, Canteen
from orders.models import Order
from menu.models import MenuItem


def landing_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Akun baru TIDAK aktif sampai admin konfirmasi
            user.is_active = False
            user.is_approved = False
            user.save()
            return redirect('register_pending')
        else:
            messages.error(request, 'Terjadi kesalahan. Cek kembali form kamu.')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username_input = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # Cek apakah user ada (via username atau email)
        from django.db.models import Q
        try:
            pending_user = CustomUser.objects.get(
                Q(username__iexact=username_input) | Q(email__iexact=username_input)
            )
            # Jika akun belum disetujui admin
            if not pending_user.is_approved and pending_user.role in ['student', 'vendor']:
                messages.warning(request, 'Akun kamu sedang menunggu konfirmasi admin. Silakan tunggu atau hubungi admin.')
                return render(request, 'accounts/login.html', {'form': LoginForm()})
            # Jika akun dinonaktifkan
            if not pending_user.is_active:
                messages.error(request, 'Akun kamu telah dinonaktifkan. Hubungi admin untuk bantuan.')
                return render(request, 'accounts/login.html', {'form': LoginForm()})
        except CustomUser.DoesNotExist:
            pass
        except CustomUser.MultipleObjectsReturned:
            pass

        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Selamat datang, {user.username}!')
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Username/email atau password salah. Periksa kembali.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Kamu berhasil logout.')
    return redirect('login')


def register_pending_view(request):
    """Halaman yang ditampilkan setelah registrasi berhasil, menunggu konfirmasi admin."""
    return render(request, 'accounts/register_pending.html')


@login_required
def dashboard_view(request):
    user = request.user
    if user.is_sysadmin():
        return redirect('admin_dashboard')
    elif user.is_vendor():
        return redirect('vendor_dashboard')
    else:
        return redirect('student_dashboard')


@login_required
def student_dashboard(request):
    if not request.user.is_student():
        return redirect('dashboard')
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    active_order = Order.objects.filter(user=request.user, status__in=['pending', 'processing']).first()
    canteens = Canteen.objects.filter(is_active=True)
    context = {
        'recent_orders': recent_orders,
        'active_order': active_order,
        'canteens': canteens,
        'total_orders': Order.objects.filter(user=request.user).count(),
    }
    return render(request, 'dashboard/student.html', context)


@login_required
def student_menu_view(request):
    if not request.user.is_student():
        return redirect('dashboard')
    
    from menu.models import Category
    from accounts.models import Canteen  # Import di sini agar selalu tersedia
    
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category', '')

    # Get active canteen from session
    selected_canteen_id = request.session.get('selected_canteen_id')
    active_canteen = None

    items = MenuItem.objects.filter(is_available=True)
    
    # If student has scanned QR, filter to that canteen only
    if selected_canteen_id:
        try:
            active_canteen = Canteen.objects.get(id=selected_canteen_id, is_active=True)
            items = items.filter(canteen=active_canteen)
        except Exception:
            # Session canteen no longer valid, clear it
            request.session.pop('selected_canteen_id', None)
            request.session.pop('selected_canteen_name', None)

    if search_query:
        items = items.filter(name__icontains=search_query)
    if category_id:
        items = items.filter(category_id=category_id)

    categories = Category.objects.all()
    canteens = Canteen.objects.filter(is_active=True)

    # Convert to int if not empty for template comparison
    selected_cat = int(category_id) if category_id and category_id.isdigit() else ''

    context = {
        'items': items,
        'categories': categories,
        'canteens': canteens,
        'search': search_query,
        'selected_cat': selected_cat,
        'active_canteen': active_canteen,
        'has_canteen_session': bool(selected_canteen_id),
    }
    return render(request, 'dashboard/menu_makanan.html', context)


@login_required
def student_menu_detail_view(request, item_id):
    if request.user.role != 'student':
        messages.error(request, 'Akses ditolak. Anda bukan student.')
        return redirect('dashboard')
    
    try:
        item = MenuItem.objects.get(id=item_id, is_available=True)
    except MenuItem.DoesNotExist:
        messages.error(request, 'Menu tidak ditemukan atau tidak tersedia.')
        return redirect('student_menu')

    context = {
        'item': item,
    }
    return render(request, 'dashboard/menu_makanan_detail.html', context)




@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil berhasil diperbarui!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


# Admin System Views
@login_required
def admin_dashboard(request):
    if not request.user.is_sysadmin():
        return redirect('dashboard')
    total_users = CustomUser.objects.count()
    total_orders = Order.objects.count()
    total_canteens = Canteen.objects.count()
    total_menu = MenuItem.objects.count()
    recent_users = CustomUser.objects.order_by('-date_joined')[:10]
    orders_by_status = {
        'pending': Order.objects.filter(status='pending').count(),
        'processing': Order.objects.filter(status='processing').count(),
        'done': Order.objects.filter(status='done').count(),
        'cancelled': Order.objects.filter(status='cancelled').count(),
    }
    context = {
        'total_users': total_users,
        'total_orders': total_orders,
        'total_canteens': total_canteens,
        'total_menu': total_menu,
        'recent_users': recent_users,
        'orders_by_status': orders_by_status,
    }
    return render(request, 'admin_panel/dashboard.html', context)


@login_required
def admin_dashboard_api(request):
    if not request.user.is_sysadmin():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    from django.utils import timezone
    from datetime import timedelta
    
    today = timezone.now().date()
    
    # 7 days users
    user_data = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        user_data.append(CustomUser.objects.filter(date_joined__date=d).count())
        
    # 10 days orders (template uses 10 bars A-J)
    order_data = []
    for i in range(9, -1, -1):
        d = today - timedelta(days=i)
        order_data.append(Order.objects.filter(created_at__date=d).count())
        
    # Hourly orders today (for target chart: 6, 8, 12, 15, 18, 20)
    hourly_orders = []
    for h in [6, 8, 12, 15, 18, 20]:
        hourly_orders.append(Order.objects.filter(created_at__date=today, created_at__hour=h).count())
        
    # Global volume 7 days (revenue)
    revenue_data = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        rev = Order.objects.filter(created_at__date=d, status='done').aggregate(t=Sum('total_price'))['t'] or 0
        revenue_data.append(float(rev))

    # Canteens top
    canteen_orders = []
    canteens = Canteen.objects.annotate(todays_orders=Count('orders', filter=Q(orders__created_at__date=today))).order_by('-todays_orders')[:9]
    for c in canteens:
        canteen_orders.append(c.todays_orders)
    while len(canteen_orders) < 9:
        canteen_orders.append(0)

    return JsonResponse({
        'total_users': CustomUser.objects.count(),
        'total_orders': Order.objects.count(),
        'total_canteens': Canteen.objects.count(),
        'chart_users': user_data,
        'chart_orders': order_data,
        'chart_canteens': canteen_orders,
        'chart_hourly': hourly_orders,
        'chart_revenue': revenue_data,
    })


@login_required
def admin_users_api(request):
    """Realtime stats untuk halaman Users"""
    if not request.user.is_sysadmin():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    from django.utils import timezone
    from datetime import timedelta
    today = timezone.now().date()
    total_active = CustomUser.objects.filter(is_active=True).count()
    total_siswa  = CustomUser.objects.filter(role='student').count()
    total_penjual = CustomUser.objects.filter(role='vendor').count()
    total_admin  = CustomUser.objects.filter(role='sysadmin').count()
    # 7-day trend data per role
    siswa_trend   = [CustomUser.objects.filter(role='student',  date_joined__date=(today - timedelta(days=i))).count() for i in range(6, -1, -1)]
    penjual_trend = [CustomUser.objects.filter(role='vendor',   date_joined__date=(today - timedelta(days=i))).count() for i in range(6, -1, -1)]
    admin_trend   = [CustomUser.objects.filter(role='sysadmin', date_joined__date=(today - timedelta(days=i))).count() for i in range(6, -1, -1)]
    active_trend  = [CustomUser.objects.filter(is_active=True,  date_joined__date=(today - timedelta(days=i))).count() for i in range(6, -1, -1)]
    return JsonResponse({
        'total_active': total_active,
        'total_siswa': total_siswa,
        'total_penjual': total_penjual,
        'total_admin': total_admin,
        'trend_active': active_trend,
        'trend_siswa': siswa_trend,
        'trend_penjual': penjual_trend,
        'trend_admin': admin_trend,
    })


@login_required
def admin_monitoring_api(request):
    """Realtime data untuk halaman Monitoring"""
    if not request.user.is_sysadmin():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Avg, F, ExpressionWrapper, DurationField
    today = timezone.now().date()
    # 4 summary cards
    total_users  = CustomUser.objects.count()
    orders_today = Order.objects.filter(created_at__date=today)
    active_queue = Order.objects.filter(status__in=['pending', 'processing']).count()
    # avg wait = avg minutes between created_at and updated_at for done orders today
    done_orders = orders_today.filter(status='done')
    total_orders_today = orders_today.count()
    # 7-day order trend
    order_trend = []
    day_labels  = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        order_trend.append(Order.objects.filter(created_at__date=d).count())
        day_labels.append(d.strftime('%d %b'))
    # Hourly today (00-23)
    hourly = [orders_today.filter(created_at__hour=h).count() for h in range(0, 24)]
    # Status breakdown today
    status_data = {
        'pending':    orders_today.filter(status='pending').count(),
        'processing': orders_today.filter(status='processing').count(),
        'done':       orders_today.filter(status='done').count(),
        'cancelled':  orders_today.filter(status='cancelled').count(),
    }
    # Top 5 menu items today
    from orders.models import OrderItem
    from menu.models import MenuItem
    from django.db.models import Sum as DSum
    top_menus = (
        OrderItem.objects
        .filter(order__created_at__date=today)
        .values('menu_item__name')
        .annotate(total_qty=DSum('quantity'))
        .order_by('-total_qty')[:5]
    )
    top_menu_list = [{'name': m['menu_item__name'], 'count': m['total_qty']} for m in top_menus]
    # Canteen active queue
    from accounts.models import Canteen
    canteens_queue = []
    for c in Canteen.objects.filter(is_active=True):
        q = Order.objects.filter(canteen=c, status__in=['pending','processing']).count()
        canteens_queue.append({'name': c.name, 'count': q})
    canteens_queue.sort(key=lambda x: x['count'], reverse=True)
    # Mini chart trends (7 days per category)
    user_trend = [CustomUser.objects.filter(date_joined__date=(today - timedelta(days=i))).count() for i in range(6, -1, -1)]
    return JsonResponse({
        'total_users': total_users,
        'orders_today': total_orders_today,
        'active_queue': active_queue,
        'day_labels': day_labels,
        'order_trend': order_trend,
        'hourly': hourly,
        'status': status_data,
        'top_menus': top_menu_list,
        'canteens_queue': canteens_queue,
        'user_trend': user_trend,
    })


@login_required
def admin_users(request):
    if not request.user.is_sysadmin():
        return redirect('dashboard')
    if request.method == 'POST':
        # Logic untuk Tambah Pengguna Baru oleh Admin
        username = request.POST.get('username')
        email = request.POST.get('email')
        role = request.POST.get('role', 'student')
        password = request.POST.get('password')
        
        if username and email and password:
            if CustomUser.objects.filter(username=username).exists():
                messages.error(request, f'Username "{username}" sudah digunakan.')
            elif CustomUser.objects.filter(email=email).exists():
                messages.error(request, f'Email "{email}" sudah digunakan.')
            else:
                # Admin menambahkan user: langsung aktif & sudah disetujui
                user = CustomUser.objects.create_user(
                    username=username, email=email, password=password, role=role,
                    is_active=True, is_approved=True
                )
                # Jika vendor, buat kantin placeholder otomatis
                if role == 'vendor':
                    Canteen.objects.create(
                        vendor=user,
                        name=f'Kantin {username}',
                        location='Lokasi belum diisi',
                        description='Kantin baru - silakan edit di halaman kantin.',
                        is_active=True,
                    )
                    messages.success(request, f'Vendor "{username}" berhasil ditambahkan beserta kantin placeholder-nya. Login: {username} / {password}')
                else:
                    messages.success(request, f'Pengguna "{username}" berhasil ditambahkan. Login: {username} / {password}')
        else:
            messages.error(request, 'Semua field (Username, Email, Password) harus diisi.')
        return redirect('admin_users')

    role_filter = request.GET.get('role', '')
    search = request.GET.get('search', '')
    users = CustomUser.objects.all().order_by('-date_joined')
    if role_filter:
        users = users.filter(role=role_filter)
    if search:
        users = users.filter(username__icontains=search) | users.filter(email__icontains=search)
        
    # Calculate statistics for the top cards
    total_active = CustomUser.objects.filter(is_active=True).count()
    total_siswa = CustomUser.objects.filter(role='student').count()
    total_penjual = CustomUser.objects.filter(role='vendor').count()
    total_admin = CustomUser.objects.filter(role='sysadmin').count()

    context = {
        'users': users, 
        'role_filter': role_filter, 
        'search': search,
        'total_active': total_active,
        'total_siswa': total_siswa,
        'total_penjual': total_penjual,
        'total_admin': total_admin
    }
    return render(request, 'admin_panel/users.html', context)


@login_required
def admin_toggle_user(request, user_id):
    if not request.user.is_sysadmin():
        return redirect('dashboard')
    user = get_object_or_404(CustomUser, id=user_id)
    # Toggle is_active dan is_approved secara bersamaan
    user.is_active = not user.is_active
    user.is_approved = user.is_active  # approved = aktif
    user.save()
    status = 'diaktifkan & dikonfirmasi' if user.is_active else 'dinonaktifkan'
    messages.success(request, f'User {user.username} berhasil {status}.')
    # Jika vendor baru diaktifkan tapi belum punya kantin, buat kantin placeholder
    if user.is_active and user.role == 'vendor' and not hasattr(user, 'canteen'):
        Canteen.objects.create(
            vendor=user,
            name=f'Kantin {user.username}',
            location='Lokasi belum diisi',
            description='Kantin baru - silakan edit.',
            is_active=True,
        )
        messages.info(request, f'Kantin placeholder untuk {user.username} juga telah dibuat.')
    return redirect('admin_users')


@login_required
def admin_canteens(request):
    if not request.user.is_sysadmin():
        return redirect('dashboard')

    # ── POST: toggle status kantin ──────────────────────────────
    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'add':
            name        = request.POST.get('name', '').strip()
            vendor_id   = request.POST.get('vendor_id', '')
            location    = request.POST.get('location', '').strip()
            description = request.POST.get('description', '').strip()
            try:
                vendor = CustomUser.objects.get(id=vendor_id, role='vendor')
                # OneToOneField: cek dulu apakah vendor sudah punya kantin
                if hasattr(vendor, 'canteen'):
                    messages.error(request, f'Vendor "{vendor.username}" sudah memiliki kantin.')
                else:
                    Canteen.objects.create(
                        name=name,
                        vendor=vendor,
                        location=location,
                        description=description,
                        is_active=True,
                    )
                    messages.success(request, f'Kantin "{name}" berhasil ditambahkan.')
            except CustomUser.DoesNotExist:
                messages.error(request, 'Vendor dengan ID tersebut tidak ditemukan atau bukan role Vendor.')
            except Exception as e:
                messages.error(request, f'Gagal menambahkan kantin: {e}')

        elif action == 'edit':
            canteen_id  = request.POST.get('canteen_id')
            name        = request.POST.get('name', '').strip()
            location    = request.POST.get('location', '').strip()
            description = request.POST.get('description', '').strip()
            try:
                kantin = get_object_or_404(Canteen, id=canteen_id)
                kantin.name        = name
                kantin.location    = location
                kantin.description = description
                kantin.save()
                messages.success(request, f'Kantin "{kantin.name}" berhasil diperbarui.')
            except Exception as e:
                messages.error(request, f'Gagal memperbarui kantin: {e}')

        elif action == 'delete':
            canteen_id = request.POST.get('canteen_id')
            try:
                kantin = get_object_or_404(Canteen, id=canteen_id)
                nama = kantin.name
                kantin.delete()
                messages.success(request, f'Kantin "{nama}" berhasil dihapus.')
            except Exception as e:
                messages.error(request, f'Gagal menghapus kantin: {e}')

        else:
            # Toggle is_active
            toggle_id = request.POST.get('toggle_id')
            if toggle_id:
                try:
                    kantin = get_object_or_404(Canteen, id=toggle_id)
                    kantin.is_active = not kantin.is_active
                    kantin.save()
                    status_text = 'diaktifkan' if kantin.is_active else 'dinonaktifkan'
                    messages.success(request, f'Kantin "{kantin.name}" berhasil {status_text}.')
                except Exception as e:
                    messages.error(request, f'Gagal mengubah status kantin: {e}')

        return redirect('admin_canteens')

    # ── GET: search & filter ────────────────────────────────────
    search        = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')

    canteens = Canteen.objects.select_related('vendor').annotate(
        menu_count=Count('menu_items', distinct=True),
        order_count=Count('orders', distinct=True)
    ).order_by('-created_at')

    if search:
        canteens = canteens.filter(
            Q(name__icontains=search) |
            Q(vendor__username__icontains=search)
        )

    if status_filter == 'aktif':
        canteens = canteens.filter(is_active=True)
    elif status_filter == 'nonaktif':
        canteens = canteens.filter(is_active=False)

    total_kantin = Canteen.objects.count()
    total_aktif  = Canteen.objects.filter(is_active=True).count()

    context = {
        'canteens': canteens,
        'search': search,
        'status_filter': status_filter,
        'total_kantin': total_kantin,
        'total_aktif': total_aktif,
    }
    return render(request, 'admin_panel/canteens.html', context)


@login_required
def admin_monitoring(request):
    if not request.user.is_sysadmin():
        return redirect('dashboard')
    from ai_features.models import AnomalyLog
    anomalies = AnomalyLog.objects.order_by('-detected_at')[:20]
    return render(request, 'admin_panel/monitoring.html', {'anomalies': anomalies})


@login_required
def admin_logs(request):
    if not request.user.is_sysadmin():
        return redirect('dashboard')
    from ai_features.models import AnomalyLog
    logs = AnomalyLog.objects.select_related('user').order_by('-detected_at')
    return render(request, 'admin_panel/logs.html', {'logs': logs})


@login_required
def admin_user_profile(request, user_id):
    if not request.user.is_sysadmin():
        return redirect('dashboard')
        
    user_profile = get_object_or_404(CustomUser, id=user_id)
    
    # Menghitung statistik pesanan
    orders = Order.objects.filter(user=user_profile).order_by('-created_at')
    total_orders = orders.count()
    total_pembelian_rp = sum(order.total_price for order in orders if order.status == 'done')
    total_pembelian_count = orders.filter(status='done').count()
    
    recent_orders = orders[:5]
    
    # Data mock untuk AI Analisis & Aktivitas
    activities = [
        {"time": "14:02", "type": "login", "text": "Login", "color": "#6eb5a8"},
        {"time": "12:15", "type": "order", "text": "Order #1233", "color": "#cbd5e1"},
        {"time": "12:30", "type": "review", "text": "Review Menu", "color": "#cbd5e1"},
        {"time": "12:30", "type": "ai", "text": "User ini menyukai...", "color": "#cbd5e1"},
    ]
    
    # Mock data for anomaly score
    anomaly_score = 2
    
    context = {
        'user_profile': user_profile,
        'total_orders': total_orders,
        'total_pembelian_rp': total_pembelian_rp,
        'total_pembelian_count': total_pembelian_count,
        'recent_orders': recent_orders,
        'activities': activities,
        'anomaly_score': anomaly_score,
    }
    
    return render(request, 'admin_panel/user_profile.html', context)


@login_required
def admin_canteen_detail(request, canteen_id):
    if not request.user.is_sysadmin():
        return redirect('dashboard')
        
    from menu.models import MenuItem, Category
    from orders.models import Order
    from django.db.models import Sum
    
    canteen = get_object_or_404(Canteen, id=canteen_id)
    menu_items = MenuItem.objects.filter(canteen=canteen).order_by('-order_count')
    
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    
    if search_query:
        menu_items = menu_items.filter(name__icontains=search_query)
    if category_filter:
        menu_items = menu_items.filter(category__name__icontains=category_filter)

    orders = Order.objects.filter(canteen=canteen).order_by('-created_at')[:20]
    
    total_menu = menu_items.count()
    total_pesanan = Order.objects.filter(canteen=canteen).count()
    revenue = Order.objects.filter(canteen=canteen, status='done').aggregate(total=Sum('total_price'))['total'] or 0
    
    context = {
        'canteen': canteen,
        'menu_items': menu_items,
        'categories': Category.objects.all(),
        'search': search_query,
        'category_filter': category_filter,
        'orders': orders,
        'total_menu': total_menu,
        'total_pesanan': total_pesanan,
        'revenue': revenue,
    }
    return render(request, 'admin_panel/canteen_detail.html', context)


@login_required
def admin_add_menu(request, canteen_id):
    if not request.user.is_sysadmin():
        return redirect('dashboard')
        
    from menu.models import MenuItem, Category
    from django.contrib import messages
    
    if request.method == 'POST':
        canteen = get_object_or_404(Canteen, id=canteen_id)
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        price = request.POST.get('price')
        image = request.FILES.get('image')
        
        try:
            category = Category.objects.get(id=category_id) if category_id else None
            MenuItem.objects.create(
                canteen=canteen,
                category=category,
                name=name,
                price=price,
                image=image,
                is_available=True
            )
            messages.success(request, f'Menu {name} berhasil ditambahkan!')
        except Exception as e:
            messages.error(request, f'Gagal menambahkan menu: {str(e)}')
            
    return redirect('admin_canteen_detail', canteen_id=canteen_id)
