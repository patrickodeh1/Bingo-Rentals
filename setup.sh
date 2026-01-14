#!/bin/bash
# Setup script for Bingo Rentals

echo "Creating superuser..."
python manage.py shell << END
from django.contrib.auth.models import User
import os

# Only create if doesn't exist
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@rentals.com', 'admin123')
    print("✓ Superuser 'admin' created with password 'admin123'")
else:
    print("✓ Superuser 'admin' already exists")

# Create pricing settings if they don't exist
from products.models import PricingSetting
pricing = PricingSetting.get_settings()
if not hasattr(pricing, 'id') or pricing.id is None:
    PricingSetting.objects.create(
        delivery_fee=79.00,
        pickup_fee=79.00,
        updated_by='System'
    )
    print("✓ Default pricing settings created")
else:
    print("✓ Pricing settings already exist")

# Create sample products if they don't exist
from products.models import Product
if Product.objects.count() == 0:
    Product.objects.create(
        name="Storage Pod",
        category="storage_pod",
        description="Portable storage units perfect for home, office, or business storage needs.",
        size_description="8ft x 5ft x 8ft (1,000 cu ft)",
        monthly_rate=149.00,
        stock_quantity=10,
        is_active=True
    )
    
    Product.objects.create(
        name="Garbage Bin",
        category="garbage_bin",
        description="Convenient garbage bin rental for temporary disposal needs.",
        size_description="10-Yard Dumpster",
        monthly_rate=99.00,
        stock_quantity=15,
        is_active=True
    )
    
    print("✓ Sample products created")
else:
    print("✓ Products already exist")

END

echo ""
echo "Setup complete!"
echo ""
echo "Access the admin panel at: http://localhost:8000/admin/"
echo "Username: admin"
echo "Password: admin123"
echo ""
echo "Update the Stripe and SendGrid keys in .env file when ready"
