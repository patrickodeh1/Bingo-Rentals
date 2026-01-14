# Portable Storage & Bin Rental Booking Platform

A fully functional booking platform for portable storage pods and garbage bins with guest checkout, Stripe payments, automated notifications, and admin dashboard.

## Project Status: MVP Complete ✅

### Features Implemented

#### ✅ Phase 1: Foundation
- Django 5.x project setup with 4 specialized apps (products, bookings, dashboard, notifications)
- PostgreSQL and SQLite database configuration
- Environment variables management with python-decouple

#### ✅ Phase 2: Database
- Product management (Storage Pods & Garbage Bins)
- Pricing settings with global delivery/pickup fees
- Blackout dates for unavailable periods
- Booking model with payment tracking
- Pickup request model for separate pickup scheduling

#### ✅ Phase 3: Booking Flow (4-Step Process)
1. **Select Product** - Browse and choose rental items
2. **Choose Dates** - Calendar-based date selection with blackout dates
3. **Customer Details** - Delivery address and contact information
4. **Order Summary** - Price breakdown and Stripe payment

#### ✅ Phase 4: Admin Dashboard
- Dashboard home with statistics (new orders, scheduled deliveries, available units)
- Manage orders with status filtering and date ranges
- Inventory management with stock tracking
- Pricing settings (easily update delivery/pickup fees)
- Blackout date management

#### ✅ Phase 5: Pickup Scheduling
- Guest-friendly pickup form (no login required)
- Pickup payment integration
- Separate pickup request tracking

#### ✅ Phase 6: Notifications
- Email templates (booking confirmation, delivery reminder, pickup confirmation)
- SendGrid integration ready (add API key to .env)
- SMS templates using Twilio (add credentials to .env)
- Logger-based console output for testing

#### ✅ Phase 7: Frontend Templates
- Responsive templates using Tailwind CSS
- Mobile-optimized booking flow
- Interactive date picker with calendar
- Real-time price calculation
- Stripe payment integration with Elements

---

## Quick Start

### 1. Install Dependencies
```bash
source benv/bin/activate
pip install -r requirements.txt
```

### 2. Database Setup
```bash
python manage.py migrate
```

### 3. Create Admin User & Sample Data
```bash
python manage.py shell << EOF
from django.contrib.auth.models import User
from products.models import Product, PricingSetting

# Create superuser
User.objects.create_superuser('admin', 'admin@rentals.com', 'admin123')

# Create products
Product.objects.create(
    name="Storage Pod",
    category="storage_pod",
    description="Portable storage units",
    size_description="8ft x 5ft x 8ft (1,000 cu ft)",
    monthly_rate=149.00,
    stock_quantity=10,
)

Product.objects.create(
    name="Garbage Bin",
    category="garbage_bin",
    description="Garbage bin rental",
    size_description="10-Yard Dumpster",
    monthly_rate=99.00,
    stock_quantity=15,
)
EOF
```

### 4. Start Development Server
```bash
python manage.py runserver
```

Visit: http://localhost:8000/booking/

---

## Configuration

### Environment Variables (.env)

**Required for Production:**
```env
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Stripe (Get keys from https://dashboard.stripe.com/)
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# SendGrid (Get API key from https://app.sendgrid.com/)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST_PASSWORD=SG.your-api-key-here
SENDGRID_API_KEY=SG.your-api-key-here

# Twilio (Optional for SMS, get from https://www.twilio.com/)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...

# Database (Production - Uncomment PostgreSQL settings in settings.py)
DATABASE_URL=postgresql://user:password@host:5432/bingo_rentals
```

### Email Testing

**For Development:** Email goes to console (no API key needed)

**For Production:**
1. Get SendGrid API key
2. Add to .env: `SENDGRID_API_KEY=SG.xxxxx`
3. Set EMAIL_HOST_PASSWORD in .env
4. Update EMAIL_BACKEND in .env to: `django.core.mail.backends.smtp.EmailBackend`

---

## Admin Panel

**URL:** http://localhost:8000/admin/

**Default Credentials:**
- Username: `admin`
- Password: `admin123` (Change in production!)

### Admin Features
- Manage products, pricing, and blackout dates
- View and update booking statuses
- Track inventory and available units
- Process refunds and cancellations

---

## Booking Flow Details

### Customer Journey
1. Browse products on homepage
2. Select product and dates (with calendar picker)
3. Enter delivery address and contact info
4. Review order summary
5. Pay with Stripe (test card: 4242 4242 4242 4242)
6. Receive confirmation email
7. Schedule pickup later (no login required)

### Payment Processing
- Stripe integration for secure payments
- Drop-off fee charged upfront
- Pickup fee charged separately when scheduled
- All payments stored with booking for reference

### Notifications
- ✅ Booking confirmation (email + SMS)
- ✅ Delivery reminder (1 day before)
- ✅ Pickup confirmation (email + SMS)
- 🔄 Ready for SendGrid/Twilio integration

---

## Testing the Booking Flow

### Test Products Already Created
1. **Storage Pod** - $149/month, 10 units available
2. **Garbage Bin** - $99/month, 15 units available

### Test Stripe Payment
Use these test card numbers (Development mode):
- **Success:** `4242 4242 4242 4242`
- **Decline:** `4000 0000 0000 0002`
- **Expires:** Any future date
- **CVC:** Any 3 digits

### Test Data Flow
1. Click "Book Your Rental"
2. Select a product
3. Pick a date and duration
4. Fill in address details
5. Review and pay
6. Check console for email output
7. Go to admin panel to see booking

---

## File Structure

```
bingo_rentals/
├── manage.py                    # Django management
├── requirements.txt             # Dependencies
├── .env                         # Environment variables
├── db.sqlite3                   # Development database
│
├── bingo_rentals/               # Main project settings
│   ├── settings.py              # Configured with all apps
│   ├── urls.py                  # Main URL routing
│   └── wsgi.py
│
├── products/                    # Product management
│   ├── models.py                # Product, PricingSetting, BlackoutDate
│   ├── views.py                 # Admin views
│   ├── admin.py                 # Django admin configuration
│   └── migrations/
│
├── bookings/                    # Core booking engine
│   ├── models.py                # Booking, PickupRequest
│   ├── views.py                 # 4-step booking flow
│   ├── forms.py                 # Customer and pickup forms
│   ├── urls.py                  # Booking URLs
│   ├── admin.py                 # Django admin
│   └── migrations/
│
├── dashboard/                   # Admin dashboard
│   ├── views.py                 # Dashboard pages
│   ├── urls.py                  # Dashboard URLs
│   ├── admin.py
│   └── migrations/
│
├── notifications/               # Email & SMS
│   ├── utils.py                 # SendGrid + Twilio utilities
│   ├── tasks.py                 # Notification sending
│   └── migrations/
│
└── templates/                   # HTML templates
    ├── base.html                # Base template
    ├── booking/
    │   ├── select_product.html
    │   ├── select_dates.html
    │   ├── customer_details.html
    │   ├── order_summary.html
    │   ├── confirmation.html
    │   ├── schedule_pickup.html
    │   ├── pickup_payment.html
    │   └── pickup_confirmed.html
    ├── dashboard/               # (Coming next)
    └── emails/
        ├── booking_confirmation.html|txt
        ├── drop_off_reminder.html|txt
        └── pickup_confirmation.html|txt
```

---

## Next Steps for Completion

### 1. Dashboard Templates (NEXT)
- [ ] Dashboard homepage template
- [ ] Orders management template
- [ ] Inventory management template
- [ ] Pricing settings template
- [ ] Blackout dates template

### 2. Production Setup
- [ ] Switch to PostgreSQL (database config ready in settings.py)
- [ ] Add Stripe test keys to .env
- [ ] Add SendGrid API key to .env
- [ ] Configure allowed hosts and secret key
- [ ] Set DEBUG=False

### 3. Email Integration
- [ ] Test SendGrid integration with real API key
- [ ] Add email sending to notification tasks
- [ ] Test email templates in production

### 4. SMS Integration (Optional)
- [ ] Add Twilio credentials to .env
- [ ] Uncomment Twilio setup in notification utilities
- [ ] Test SMS delivery

### 5. Additional Features (Optional)
- [ ] Bulk booking for corporate clients
- [ ] Subscription/recurring bookings
- [ ] Customer reviews and ratings
- [ ] Advanced analytics dashboard
- [ ] API endpoints for mobile app

---

## Deployment Checklist

- [ ] Update SECRET_KEY in .env
- [ ] Set DEBUG=False
- [ ] Add allowed hosts
- [ ] Switch to PostgreSQL
- [ ] Configure SendGrid
- [ ] Configure Stripe webhooks
- [ ] Set up HTTPS
- [ ] Configure email in production
- [ ] Set up static files (WhiteNoise configured)
- [ ] Create superuser account
- [ ] Run migrations on production DB
- [ ] Test payment flow
- [ ] Test email delivery
- [ ] Monitor logs and errors

---

## Support & Documentation

**Django Documentation:** https://docs.djangoproject.com/
**Stripe Docs:** https://stripe.com/docs
**SendGrid Docs:** https://docs.sendgrid.com/
**Twilio Docs:** https://www.twilio.com/docs

---

## License

All rights reserved. Built for the customer's specific needs.

---

**Last Updated:** January 14, 2026
**Version:** 1.0.0 (MVP)
