Auto_Ria Service

Features

Installation
Python3 must be already installed.

git clone https://github.com/InnaKushnir/auto_ria
cd auto_ria
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

    Copy .env.sample -> .env and populate with all required data.

Run the following necessary commands

python manage.py migrate

    Docker is used to run a Redis container that is used as a broker for Celery.

docker run -d -p 6379:6379 redis

The Celery library is used to schedule tasks and launch workers.

    Starting the Celery worker is done with the command.

celery -A app worker -l INFO

    The Celery scheduler is configured as follows.

celery -A app beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler

    Create schedule for running sync in DB.

python manage.py runserver

How to run with Docker:

    Copy .env.sample -> .env and populate with all required data
    docker-compose up --build
    Create admin user & Create schedule for running sync in DB
    Run app: python manage.py runserver
