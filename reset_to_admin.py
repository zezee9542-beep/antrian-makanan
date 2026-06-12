import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "foodqueue.settings")
django.setup()

from accounts.models import CustomUser, Canteen
from menu.models import Category, MenuItem
from orders.models import Order, Cart

def run():
    # Delete everything except admin
    CustomUser.objects.exclude(role='sysadmin').delete()
    print("Deleted all users except admin.")
    
    # Check if admin exists, if not create
    if not CustomUser.objects.filter(role='sysadmin').exists():
        admin = CustomUser.objects.create(username='admin', email='admin@example.com', role='sysadmin', is_staff=True, is_superuser=True, is_active=True, is_approved=True)
        admin.set_password('admin123')
        admin.save()
        print("Created admin user.")

if __name__ == '__main__':
    run()
