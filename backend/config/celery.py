"""
Celery configuration for Plataforma Estetica
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('plataforma_estetica')

# Load config from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Periodic tasks configuration
app.conf.beat_schedule = {
    # Send appointment reminders 24 hours before
    'send-24h-reminders': {
        'task': 'apps.notificaciones.tasks.send_24h_reminders',
        'schedule': crontab(hour=9, minute=0),  # Every day at 9 AM
    },
    # Send appointment reminders 2 hours before
    'send-2h-reminders': {
        'task': 'apps.notificaciones.tasks.send_2h_reminders',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    # Check low inventory levels
    'check-low-inventory': {
        'task': 'apps.inventario.tasks.check_low_inventory',
        'schedule': crontab(hour=8, minute=0),  # Every day at 8 AM
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
