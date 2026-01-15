from bookings.models import Booking, PickupRequest
from .utils import send_email_notification, send_sms_notification
from celery import shared_task
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
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
            message=sms_message,
            country_code=booking.country_code
        )
        
        if sms_sent:
            booking.confirmation_sms_sent = True
        
        booking.save()
        
    except Exception as e:
        logger.error(f'Error sending booking confirmation for {booking_id}: {str(e)}')


@shared_task
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
            message=sms_message,
            country_code=booking.country_code
        )
        
        booking.save()
        
    except Exception as e:
        logger.error(f'Error sending drop-off reminder for {booking_id}: {str(e)}')


@shared_task
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
            message=sms_message,
            country_code=booking.country_code
        )
        
        if sms_sent:
            pickup.pickup_sms_sent = True
        
        pickup.save()
        
    except Exception as e:
        logger.error(f'Error sending pickup confirmation for {pickup_request_id}: {str(e)}')


@shared_task
def send_pickup_reminder(pickup_request_id):
    """Send reminder 1 day before pickup"""
    try:
        pickup = PickupRequest.objects.select_related('booking__product').get(id=pickup_request_id)
        booking = pickup.booking
        
        context = {
            'booking': booking,
            'pickup': pickup,
            'site_name': 'Rental Services',
        }
        
        email_sent = send_email_notification(
            subject=f'Pickup Reminder - {booking.booking_id}',
            to_email=booking.customer_email,
            template_name='pickup_reminder',
            context=context
        )
        
        if email_sent:
            pickup.pickup_email_sent = True
        
        sms_message = f"Reminder: Pickup scheduled for tomorrow at {pickup.pickup_address or booking.delivery_address}"
        
        sms_sent = send_sms_notification(
            to_phone=booking.customer_phone,
            message=sms_message,
            country_code=booking.country_code
        )
        
        pickup.save()
        
    except Exception as e:
        logger.error(f'Error sending pickup reminder for {pickup_request_id}: {str(e)}')


@shared_task
def send_daily_drop_off_reminders():
    """Send drop-off reminders for all bookings with delivery tomorrow"""
    try:
        tomorrow = datetime.now().date() + timedelta(days=1)
        
        # Get all bookings with drop-off date tomorrow that haven't had reminder sent
        bookings = Booking.objects.filter(
            drop_off_date=tomorrow,
            drop_off_reminder_sent=False
        )
        
        logger.info(f"Sending drop-off reminders to {bookings.count()} bookings")
        
        for booking in bookings:
            send_drop_off_reminder.delay(booking.id)
            
    except Exception as e:
        logger.error(f'Error in send_daily_drop_off_reminders: {str(e)}')


@shared_task
def send_daily_pickup_reminders():
    """Send pickup reminders for all pickups with date tomorrow"""
    try:
        tomorrow = datetime.now().date() + timedelta(days=1)
        
        # Get all pickups with requested_pickup_date tomorrow that haven't had reminder sent
        pickups = PickupRequest.objects.filter(
            requested_pickup_date=tomorrow,
            pickup_email_sent=False
        )
        
        logger.info(f"Sending pickup reminders to {pickups.count()} pickups")
        
        for pickup in pickups:
            send_pickup_reminder.delay(pickup.id)
            
    except Exception as e:
        logger.error(f'Error in send_daily_pickup_reminders: {str(e)}')
