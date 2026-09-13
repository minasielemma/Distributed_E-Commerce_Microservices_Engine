import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'order_project.settings')

app = Celery('order_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'poll-outbox-events-every-5-seconds': {
        'task': 'orders.tasks.process_outbox_events',
        'schedule': 5.0,
    },
}
