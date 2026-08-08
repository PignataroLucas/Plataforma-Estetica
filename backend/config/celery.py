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
    # Import sales from Conto. The window overlaps the previous run and
    # duplicates are deduplicated by voucher id, so a missed run self-corrects.
    'import-conto-sales': {
        'task': 'apps.integraciones.tasks.import_conto_sales',
        'schedule': crontab(minute='*/15'),
    },
    # Pull catalog state (stock and cost) from Conto
    'sync-conto-stock': {
        'task': 'apps.integraciones.tasks.sync_conto_stock',
        'schedule': crontab(minute='0,30'),
    },
    # Re-check that each integration still resolves to its linked account.
    # The per-sync tripwire only fires when there is data to pull.
    'verify-conto-links': {
        'task': 'apps.integraciones.tasks.verify_conto_links',
        'schedule': crontab(hour=7, minute=30),
    },
    # Push notifications. These mirror what the `procesar_notificaciones`
    # command does; production runs the command from Railway cron because the
    # deploy has no Celery worker. Keeping both wired to the same functions
    # means dev and prod cannot drift.
    'notificaciones-disparadores': {
        'task': 'apps.notificaciones.tasks.correr_disparadores_task',
        'schedule': crontab(minute='*/15'),
    },
    'notificaciones-cola': {
        'task': 'apps.notificaciones.tasks.procesar_cola_push_task',
        'schedule': crontab(minute='*/5'),
    },
    'notificaciones-recibos': {
        'task': 'apps.notificaciones.tasks.procesar_recibos_push_task',
        'schedule': crontab(minute='*/30'),
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
