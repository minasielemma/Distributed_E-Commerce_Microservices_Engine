import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recommendation_project.settings')

app = Celery('recommendation_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'precompute-recommendations-every-30-min': {
        'task': 'recommendations.tasks.precompute_recommendations',
        'schedule': crontab(minute='*/30'),
    },
    'sync-product-metadata-every-10-min': {
        'task': 'recommendations.tasks.sync_product_metadata',
        'schedule': crontab(minute='*/10'),
    },
}
