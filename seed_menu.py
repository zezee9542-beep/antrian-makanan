"""
Seed script untuk mengisi data menu makanan demo.
Jalankan: python seed_menu.py
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "foodqueue.settings")
django.setup()

from accounts.models import CustomUser, Canteen
from menu.models import Category, MenuItem


def run():
    print("Seeding categories dan menu items...")

    # Pastikan user sudah ada
    try:
        vendor1 = CustomUser.objects.get(username='vendor1')
        vendor2 = CustomUser.objects.get(username='vendor2')
        canteen1 = Canteen.objects.get(vendor=vendor1)
        canteen2 = Canteen.objects.get(vendor=vendor2)
    except Exception as e:
        print(f"Error: {e}")
        print("Jalankan seed_users.py terlebih dahulu!")
        return

    # Buat Kategori
    makanan_berat, _ = Category.objects.get_or_create(name='Makanan Berat', defaults={'icon': '🍛'})
    minuman, _ = Category.objects.get_or_create(name='Minuman', defaults={'icon': '🥤'})
    snack, _ = Category.objects.get_or_create(name='Snack & Gorengan', defaults={'icon': '🍟'})
    dessert, _ = Category.objects.get_or_create(name='Dessert', defaults={'icon': '🍰'})

    print("✓ Kategori berhasil dibuat")

    # ====== MENU KANTIN 1 (Bu Tini) ======
    menus_kantin1 = [
        {'name': 'Nasi Goreng Spesial', 'category': makanan_berat, 'price': 15000, 'description': 'Nasi goreng dengan telur, ayam, dan sayuran segar'},
        {'name': 'Mie Ayam Bakso', 'category': makanan_berat, 'price': 13000, 'description': 'Mie ayam dengan bakso lembut dan kuah gurih'},
        {'name': 'Soto Ayam', 'category': makanan_berat, 'price': 12000, 'description': 'Soto ayam kampung dengan kuah bening segar'},
        {'name': 'Nasi Uduk Komplit', 'category': makanan_berat, 'price': 17000, 'description': 'Nasi uduk dengan lauk lengkap dan sambal'},
        {'name': 'Es Teh Manis', 'category': minuman, 'price': 4000, 'description': 'Teh manis segar dengan es batu'},
        {'name': 'Es Jeruk', 'category': minuman, 'price': 5000, 'description': 'Jeruk peras segar dengan es batu'},
        {'name': 'Jus Alpukat', 'category': minuman, 'price': 8000, 'description': 'Jus alpukat creamy dengan susu kental manis'},
        {'name': 'Tahu Goreng', 'category': snack, 'price': 3000, 'description': 'Tahu goreng crispy dengan bumbu kecap'},
        {'name': 'Tempe Goreng', 'category': snack, 'price': 2500, 'description': 'Tempe goreng renyah'},
        {'name': 'Bakwan Sayur', 'category': snack, 'price': 2000, 'description': 'Bakwan sayuran segar goreng crispy'},
    ]

    for menu_data in menus_kantin1:
        obj, created = MenuItem.objects.get_or_create(
            canteen=canteen1,
            name=menu_data['name'],
            defaults={
                'category': menu_data['category'],
                'price': menu_data['price'],
                'description': menu_data['description'],
                'is_available': True,
                'order_count': 0,
            }
        )
        if created:
            print(f"  + {obj.name} (Kantin Bu Tini)")

    # ====== MENU KANTIN 2 (Pak Budi) ======
    menus_kantin2 = [
        {'name': 'Ayam Bakar', 'category': makanan_berat, 'price': 20000, 'description': 'Ayam bakar bumbu kecap dengan lalapan segar'},
        {'name': 'Gado-Gado', 'category': makanan_berat, 'price': 12000, 'description': 'Gado-gado dengan bumbu kacang khas'},
        {'name': 'Pecel Lele', 'category': makanan_berat, 'price': 15000, 'description': 'Lele goreng dengan sambal terasi dan lalapan'},
        {'name': 'Nasi Rawon', 'category': makanan_berat, 'price': 18000, 'description': 'Rawon daging sapi dengan kuah hitam kluwek'},
        {'name': 'Es Dawet', 'category': minuman, 'price': 6000, 'description': 'Dawet tradisional dengan santan dan gula merah'},
        {'name': 'Es Campur', 'category': minuman, 'price': 7000, 'description': 'Es campur dengan berbagai topping'},
        {'name': 'Kopi Susu', 'category': minuman, 'price': 6000, 'description': 'Kopi susu hangat yang nikmat'},
        {'name': 'Pisang Goreng', 'category': snack, 'price': 5000, 'description': 'Pisang goreng crispy 3 pcs'},
        {'name': 'Risoles Mayo', 'category': snack, 'price': 4000, 'description': 'Risoles isi ragout dengan saus mayo'},
        {'name': 'Puding Coklat', 'category': dessert, 'price': 5000, 'description': 'Puding coklat lembut dengan saus vanilla'},
        {'name': 'Kue Lapis', 'category': dessert, 'price': 4000, 'description': 'Kue lapis tradisional warna-warni'},
    ]

    for menu_data in menus_kantin2:
        obj, created = MenuItem.objects.get_or_create(
            canteen=canteen2,
            name=menu_data['name'],
            defaults={
                'category': menu_data['category'],
                'price': menu_data['price'],
                'description': menu_data['description'],
                'is_available': True,
                'order_count': 0,
            }
        )
        if created:
            print(f"  + {obj.name} (Kantin Pak Budi)")

    total = MenuItem.objects.count()
    print(f"\n✓ Seeding selesai! Total {total} menu item tersedia.")
    print(f"  Kantin 1 (Bu Tini): {MenuItem.objects.filter(canteen=canteen1).count()} menu")
    print(f"  Kantin 2 (Pak Budi): {MenuItem.objects.filter(canteen=canteen2).count()} menu")


if __name__ == '__main__':
    run()
