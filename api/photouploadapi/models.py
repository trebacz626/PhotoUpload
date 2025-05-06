from django.db import models

# Create your models here.

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    email = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    logged_in = models.BooleanField(default=False)

    def __str__(self):
        return self.email


class Landmark(models.Model):
    landmark_id = models.AutoField(primary_key=True)
    photo_id = models.ImageField(upload_to='landmark_photos/')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    processed = models.BooleanField(default=False)

    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    formatted_address = models.CharField(max_length=50, null=True, blank=True)
    street_number = models.SmallIntegerField(null=True, blank=True)
    route = models.CharField(max_length=30, null=True, blank=True)
    neighborhood = models.CharField(max_length=30, null=True, blank=True)
    sublocality = models.CharField(max_length=30, null=True, blank=True)
    state = models.CharField(max_length=30, null=True, blank=True)
    district = models.CharField(max_length=30, null=True, blank=True)
    country = models.CharField(max_length=30, null=True, blank=True)
    postal_code = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return f"Landmark {self.landmark_id} by User {self.user.email}"
