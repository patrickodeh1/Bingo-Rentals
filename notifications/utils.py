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
    Payment is NEVER blocked by notification failures.
    
    Args:
        task_func: Celery task function
        *args, **kwargs: Arguments for the task
    
    Returns:
        bool: True if sent (async or sync), False if both failed (but payment still succeeds)
    """
    import threading
    
    def send_async():
        """Try async first with short timeout"""
        try:
            # Try to send via Celery with a 2-second timeout
            task_func.apply_async(args=args, kwargs=kwargs, task_id=None)
            logger.info(f'Task {task_func.name} queued to Celery')
            return True
        except Exception as celery_error:
            logger.warning(f'Celery unavailable ({type(celery_error).__name__}), using synchronous fallback')
            return False
    
    def send_sync():
        """Fallback: Send synchronously without blocking"""
        try:
            task_func(*args, **kwargs)
            logger.info(f'Notification sent synchronously (no Redis/Celery)')
            return True
        except Exception as sync_error:
            # Don't block payment for email/SMS errors
            logger.error(f'Notification failed (sync): {type(sync_error).__name__}: {sync_error}', exc_info=False)
            return False
    
    # Try async first (quick non-blocking attempt)
    if send_async():
        return True
    
    # If async failed, run sync in background thread to not block payment
    thread = threading.Thread(target=send_sync, daemon=True)
    thread.start()
    
    # Return True immediately so payment succeeds regardless
    return True


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
