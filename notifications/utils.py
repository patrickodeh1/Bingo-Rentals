from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from twilio.rest import Client
import logging

logger = logging.getLogger(__name__)


def send_notification_safe(task_func, *args, **kwargs):
    """
    Safely send notification via Celery with synchronous fallback.
    If Celery/Redis not available, sends synchronously.
    Payment is never blocked by notification failures.
    
    Args:
        task_func: Celery task function
        *args, **kwargs: Arguments for the task
    
    Returns:
        bool: True if sent (async or sync), False if both failed
    """
    try:
        # Try to send via Celery (async)
        task_func.delay(*args, **kwargs)
        logger.info(f'Task {task_func.name} queued successfully')
        return True
    except Exception as celery_error:
        # Celery failed, try synchronous fallback
        logger.warning(f'Celery task {task_func.name} failed, using synchronous fallback: {celery_error}')
        try:
            # Call the task function directly (synchronously)
            task_func(*args, **kwargs)
            logger.info(f'Notification sent synchronously (Redis/Celery unavailable)')
            return True
        except Exception as sync_error:
            # Both async and sync failed, log but don't block payment
            logger.error(f'Notification failed (both async and sync): {sync_error}')
            return False


def send_email_notification(subject, to_email, template_name, context):
    """Send HTML email notification using SendGrid"""
    try:
        html_content = render_to_string(f'emails/{template_name}.html', context)
        text_content = render_to_string(f'emails/{template_name}.txt', context)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f'Email sent to {to_email}: {subject}')
        return True
    except Exception as e:
        logger.error(f'Email sending failed to {to_email}: {str(e)}')
        return False


def send_sms_notification(to_phone, message, country_code='+1'):
    """Send SMS notification via Twilio"""
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # Format phone number - remove formatting chars
        cleaned_phone = to_phone.replace("-", "").replace("(", "").replace(")", "").replace(" ", "")
        
        # Combine country code + phone number
        full_phone = f'{country_code}{cleaned_phone}'
        
        message_obj = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=full_phone
        )
        
        logger.info(f'SMS sent to {full_phone}: {message_obj.sid}')
        return True
    except Exception as e:
        logger.error(f'SMS sending failed to {to_phone}: {str(e)}')
        return False
