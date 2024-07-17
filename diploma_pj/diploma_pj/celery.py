from __future__ import absolute_import, unicode_literals

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "diploma_pj.settings")

app = Celery("diploma_pj", broker_connection_retry_on_startup=True)
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """A debug celery task"""
    print(f"Request: {self.request!r}")
