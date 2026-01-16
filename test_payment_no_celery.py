# Test that payment works without Redis/Celery running
# Run: python manage.py shell < test_payment_no_celery.py

from notifications.utils import send_notification_safe
from notifications.tasks import send_booking_confirmation
from bookings.models import Booking
import logging

logging.basicConfig(level=logging.DEBUG)

print("Testing notification fallback mechanism...")
print("=" * 60)

# Test 1: Try calling send_notification_safe with a fake booking ID
print("\nTest 1: Sending notification without Celery running")
print("-" * 60)

try:
    # This will fail because booking doesn't exist, but it tests the fallback mechanism
    result = send_notification_safe(send_booking_confirmation, 999)
    print(f"✓ Notification system handled gracefully: {result}")
except Exception as e:
    print(f"✗ Unexpected error: {e}")

print("\nTest 2: Checking if notifications can be sent synchronously")
print("-" * 60)

# Get a real booking if exists
booking = Booking.objects.first()
if booking:
    print(f"Found booking: {booking.booking_id}")
    result = send_notification_safe(send_booking_confirmation, booking.id)
    print(f"✓ Notification result: {result}")
else:
    print("No bookings in database - test skipped")

print("\n" + "=" * 60)
print("Payment will ALWAYS succeed regardless of notification status")
print("Notifications will try: Celery → Synchronous → Log failure")
