import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bingo_rentals.settings')

app = Celery('bingo_rentals')

# Load configuration from Django settings, all configuration keys should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django app configs.
app.autodiscover_tasks()

# Configure periodic tasks (beat schedule)
app.conf.beat_schedule = {
    # Send drop-off reminders daily at 9:00 AM
    'send-drop-off-reminders': {
        'task': 'notifications.tasks.send_daily_drop_off_reminders',
        'schedule': crontab(hour=9, minute=0),
    },
    # Send pickup reminders daily at 9:00 AM
    'send-pickup-reminders': {
        'task': 'notifications.tasks.send_daily_pickup_reminders',
        'schedule': crontab(hour=9, minute=0),
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
