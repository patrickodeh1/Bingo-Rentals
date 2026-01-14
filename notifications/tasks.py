from bookings.models import Booking, PickupRequest
from .utils import send_email_notification, send_sms_notification
import logging

logger = logging.getLogger(__name__)


def send_booking_confirmation(booking_id):
    """Send booking confirmation email and SMS"""
    try:
        booking = Booking.objects.select_related('product').get(id=booking_id)
        
        # Email notification
        context = {
            'booking': booking,
            'site_name': 'Rental Services',
        }
        
        email_sent = send_email_notification(
            subject=f'Booking Confirmed - {booking.booking_id}',
            to_email=booking.customer_email,
            template_name='booking_confirmation',
            context=context
        )
        
        if email_sent:
            booking.confirmation_email_sent = True
        
        # SMS notification
        sms_message = f"Your rental is confirmed! Delivery on {booking.drop_off_date.strftime('%b %d')}. Booking ID: {booking.booking_id}"
        
        sms_sent = send_sms_notification(
            to_phone=booking.customer_phone,
            message=sms_message
        )
        
        if sms_sent:
            booking.confirmation_sms_sent = True
        
        booking.save()
        
    except Exception as e:
        logger.error(f'Error sending booking confirmation for {booking_id}: {str(e)}')


def send_drop_off_reminder(booking_id):
    """Send reminder 1 day before drop-off"""
    try:
        booking = Booking.objects.select_related('product').get(id=booking_id)
        
        context = {
            'booking': booking,
            'site_name': 'Rental Services',
        }
        
        email_sent = send_email_notification(
            subject=f'Delivery Tomorrow - {booking.product.name}',
            to_email=booking.customer_email,
            template_name='drop_off_reminder',
            context=context
        )
        
        if email_sent:
            booking.drop_off_reminder_sent = True
        
        sms_message = f"Reminder: Your {booking.product.name} will be delivered tomorrow at {booking.delivery_address}"
        
        sms_sent = send_sms_notification(
            to_phone=booking.customer_phone,
            message=sms_message
        )
        
        booking.save()
        
    except Exception as e:
        logger.error(f'Error sending drop-off reminder for {booking_id}: {str(e)}')


def send_pickup_confirmation(pickup_request_id):
    """Send pickup confirmation"""
    try:
        pickup = PickupRequest.objects.select_related('booking__product').get(id=pickup_request_id)
        booking = pickup.booking
        
        context = {
            'booking': booking,
            'pickup': pickup,
            'site_name': 'Rental Services',
        }
        
        email_sent = send_email_notification(
            subject=f'Pickup Scheduled - {booking.booking_id}',
            to_email=booking.customer_email,
            template_name='pickup_confirmation',
            context=context
        )
        
        if email_sent:
            pickup.pickup_email_sent = True
        
        sms_message = f"Pickup scheduled for {pickup.requested_pickup_date.strftime('%b %d')}. We'll collect your {booking.product.name}."
        
        sms_sent = send_sms_notification(
            to_phone=booking.customer_phone,
            message=sms_message
        )
        
        if sms_sent:
            pickup.pickup_sms_sent = True
        
        pickup.save()
        
    except Exception as e:
        logger.error(f'Error sending pickup confirmation for {pickup_request_id}: {str(e)}')
