import datetime
import os
import subprocess

from celery import shared_task
from auto.scraper import run_scraper, create_postgres_dump


@shared_task
def run_sync_with_data():
    run_scraper()
    create_postgres_dump()
