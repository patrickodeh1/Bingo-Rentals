# Celery Setup Guide for Bingo Rentals

This document explains how to run and test the Celery task queue system for scheduled email reminders.

## Architecture

The system uses:
- **Celery 5.3.4**: Async task queue for handling email/SMS notifications
- **Redis 5.0.1**: Message broker for Celery tasks
- **django-celery-beat 2.5.0**: Periodic task scheduler

## Tasks Configured

### Async Tasks (triggered on demand)
1. `send_booking_confirmation()` - Sent when customer completes booking
2. `send_drop_off_reminder()` - Sent 1 day before delivery date
3. `send_pickup_confirmation()` - Sent when pickup is scheduled
4. `send_pickup_reminder()` - Sent 1 day before pickup date

### Scheduled Tasks (run daily at 9:00 AM UTC)
1. `send_daily_drop_off_reminders()` - Finds all bookings with delivery tomorrow and sends reminders
2. `send_daily_pickup_reminders()` - Finds all pickups scheduled for tomorrow and sends reminders

## Local Development Setup

### 1. Ensure Redis is running

**Option A: Using Docker (recommended)**
```bash
docker run -d -p 6379:6379 redis:latest
```

**Option B: Using system package manager**

Ubuntu/Debian:
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
```

Mac (with Homebrew):
```bash
brew install redis
brew services start redis
```

### 2. Start the Celery Worker

In one terminal, navigate to project directory and run:

```bash
# Activate virtual environment
source benv/bin/activate

# Start celery worker in debug mode
celery -A bingo_rentals worker -l info
```

Output should show:
```
 -------------- celery@hostname v5.3.4 (sun)
--- ***** -----
 ---------- [config]
 --------- app:bingo_rentals:0x...
 -------- concurrency=8
  --------- ...
 [tasks]
  . notifications.tasks.send_booking_confirmation
  . notifications.tasks.send_daily_drop_off_reminders
  . notifications.tasks.send_daily_pickup_reminders
  . notifications.tasks.send_drop_off_reminder
  . notifications.tasks.send_pickup_confirmation
  . notifications.tasks.send_pickup_reminder

[2024-01-01 12:00:00,000: INFO/MainProcess] celery@hostname ready.
```

### 3. Start the Celery Beat Scheduler

In another terminal:

```bash
# Activate virtual environment
source benv/bin/activate

# Start celery beat scheduler
celery -A bingo_rentals beat -l info
```

Output should show scheduled tasks running at specified times:
```
celery beat v5.3.4 (sun) is starting.
... [2024-01-01 12:00:00,000: INFO/MainProcess] Scheduler: Sending due task send-drop-off-reminders ...
... [2024-01-01 12:00:00,000: INFO/MainProcess] Scheduler: Sending due task send-pickup-reminders ...
```

### 4. Run Django development server

In a third terminal:

```bash
source benv/bin/activate
python manage.py runserver
```

## Testing

### Testing Async Tasks

1. Make a booking in the application
2. Check the Celery worker terminal - you should see:
   ```
   [2024-01-01 12:00:00,000: INFO/MainProcess] Task notifications.tasks.send_booking_confirmation[...] received
   [2024-01-01 12:00:00,123: INFO/MainProcess] Task notifications.tasks.send_booking_confirmation[...] succeeded
   ```

3. Verify the email was sent (check SendGrid dashboard or email)

### Testing Scheduled Tasks

The tasks run daily at 9:00 AM UTC. To test immediately:

**Option 1: Use Django shell**
```bash
python manage.py shell
from notifications.tasks import send_daily_drop_off_reminders, send_daily_pickup_reminders
send_daily_drop_off_reminders.delay()
send_daily_pickup_reminders.delay()
```

**Option 2: Use Celery task view**
```bash
# In Django shell or management command
from bookings.models import Booking
from datetime import datetime, timedelta
from notifications.tasks import send_daily_drop_off_reminders

# Create test data: booking with drop_off_date = tomorrow
tomorrow = datetime.now().date() + timedelta(days=1)
Booking.objects.create(
    customer_email='test@example.com',
    drop_off_date=tomorrow,
    drop_off_reminder_sent=False,
    ...
)

# Trigger task
send_daily_drop_off_reminders.delay()
```

## Monitoring

### Celery Flower (Optional)

For a web-based monitoring dashboard:

```bash
pip install flower
celery -A bingo_rentals events
# In another terminal:
flower --port=5555
```

Visit http://localhost:5555 to see real-time task execution

### Celery Command Line

View active tasks:
```bash
celery -A bingo_rentals inspect active
```

View scheduled tasks:
```bash
celery -A bingo_rentals inspect scheduled
```

## Production Deployment (PythonAnywhere)

### Prerequisites
- Redis add-on enabled in PythonAnywhere
- Updated .env with Redis connection details

### 1. Update .env with Redis Connection

```
CELERY_BROKER_URL=redis://username:password@your-redis-host:6379/0
CELERY_RESULT_BACKEND=redis://username:password@your-redis-host:6379/0
```

### 2. Configure systemd Services (if available) or Use Web Apps Tab

Create `/etc/systemd/system/celery-worker.service`:
```ini
[Unit]
Description=Celery Worker Service
After=network.target

[Service]
Type=forking
User=youruser
WorkingDirectory=/home/youruser/bingo_rentals
Environment="PATH=/home/youruser/bingo_rentals/benv/bin"
ExecStart=/home/youruser/bingo_rentals/benv/bin/celery -A bingo_rentals worker --loglevel=info

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/celery-beat.service`:
```ini
[Unit]
Description=Celery Beat Scheduler Service
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/bingo_rentals
Environment="PATH=/home/youruser/bingo_rentals/benv/bin"
ExecStart=/home/youruser/bingo_rentals/benv/bin/celery -A bingo_rentals beat --loglevel=info

[Install]
WantedBy=multi-user.target
```

Enable and start services:
```bash
sudo systemctl enable celery-worker celery-beat
sudo systemctl start celery-worker celery-beat
```

### 3. Verify in PythonAnywhere Console

```bash
# Check status
celery -A bingo_rentals inspect ping

# View active tasks
celery -A bingo_rentals inspect active
```

## Troubleshooting

### "Redis connection refused"
- Ensure Redis is running: `redis-cli ping` (should return PONG)
- Check Redis connection string in settings.py

### "No module named 'celery'"
- Activate virtual environment: `source benv/bin/activate`
- Install requirements: `pip install -r requirements.txt`

### Tasks not executing
- Verify worker is running (check terminal for "ready" message)
- Verify beat scheduler is running
- Check Django logs for task execution details

### Tasks stuck in pending state
- Restart worker: `Ctrl+C` then run again
- Clear Redis queue: `redis-cli FLUSHALL` (be careful in production!)

## Email Sending Notes

The notification system uses SendGrid SMTP for email delivery:
- Emails are sent asynchronously (non-blocking)
- SMS notifications use Twilio (requires valid credentials)
- All templates are in `templates/emails/` with HTML + TXT versions
- Failed sends are logged but don't stop task execution

## Next Steps

1. ✅ Complete local testing with Redis and Celery
2. ✅ Verify scheduled tasks execute at 9:00 AM UTC
3. ✅ Test with real booking data
4. Deploy to PythonAnywhere with Redis add-on
5. Monitor task execution in production
