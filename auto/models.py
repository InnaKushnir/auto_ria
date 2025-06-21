from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator


class Auto(models.Model):
    url = models.URLField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    price_usd = models.IntegerField()
    odometer = models.IntegerField()
    username = models.CharField(max_length=255)
    phone_number = models.CharField(
        max_length=16,
        validators=[
            RegexValidator(regex=r'^\+?1?\d{9,15}$', )
        ]
    )

    image_url = models.URLField(max_length=255, unique=True)
    images_count = models.IntegerField()
    car_number = models.CharField(unique=True, max_length=20)
    car_vin = models.CharField(max_length=255)
    datetime_found = models.DateTimeField()


    def __str__(self) -> str:
        return self.title
