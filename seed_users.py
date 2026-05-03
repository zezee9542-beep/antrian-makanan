import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "foodqueue.settings")
django.setup()

from accounts.models import CustomUser, Canteen

def run():
    print("Seeding users...")
    
    # 1. SYSADMIN
    admin, created = CustomUser.objects.get_or_create(username='admin')
    admin.set_password('admin123')
    admin.email = 'admin@example.com'
    admin.role = 'sysadmin'
    admin.is_staff = True
    admin.is_superuser = True
    admin.save()
    print("Created Admin: admin / admin123")

    # 2. VENDOR
    vendor1, created = CustomUser.objects.get_or_create(username='vendor1')
    vendor1.set_password('vendor123')
    vendor1.email = 'vendor1@example.com'
    vendor1.role = 'vendor'
    vendor1.save()
    
    canteen, created = Canteen.objects.get_or_create(vendor=vendor1, defaults={'name': 'Kantin Bu Tini', 'location': 'Lantai 1, Blok A'})
    print("Created Vendor: vendor1 / vendor123 (Kantin: Kantin Bu Tini)")

    vendor2, created = CustomUser.objects.get_or_create(username='vendor2')
    vendor2.set_password('vendor123')
    vendor2.email = 'vendor2@example.com'
    vendor2.role = 'vendor'
    vendor2.save()
    
    canteen2, created = Canteen.objects.get_or_create(vendor=vendor2, defaults={'name': 'Kantin Pak Budi', 'location': 'Lantai 1, Blok B'})
    print("Created Vendor: vendor2 / vendor123 (Kantin: Kantin Pak Budi)")

    # 3. STUDENT
    student1, created = CustomUser.objects.get_or_create(username='student1')
    student1.set_password('student123')
    student1.email = 'student1@example.com'
    student1.role = 'student'
    student1.save()
    print("Created Student: student1 / student123")

    student2, created = CustomUser.objects.get_or_create(username='student2')
    student2.set_password('student123')
    student2.email = 'student2@example.com'
    student2.role = 'student'
    student2.save()
    print("Created Student: student2 / student123")

    print("Seeding completed successfully!")

if __name__ == '__main__':
    run()
