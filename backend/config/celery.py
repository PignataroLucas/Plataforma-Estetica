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
    # Process pending reminders (24h and 2h before appointments)
    'procesar-recordatorios-turnos': {
        'task': 'apps.notificaciones.tasks.procesar_recordatorios_pendientes',
        'schedule': crontab(minute=0),  # Every hour on the hour
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
