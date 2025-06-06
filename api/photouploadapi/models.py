from django.db import models
from django.contrib.auth.models import User


from django.db import models
from django.conf import settings 
import uuid

class Photo(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='photos')
    gcs_blob_name = models.CharField(max_length=255, unique=True, help_text="Name of the file in Google Cloud Storage")
    upload_time = models.DateTimeField(auto_now_add=True)
    PROCESSING_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    processing_status = models.CharField(
        max_length=20,
        choices=PROCESSING_STATUS_CHOICES,
        default='pending'
    )
    original_filename = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Photo {self.id} by {self.user.username}"

class Landmark(models.Model):
    photo = models.OneToOneField(Photo, on_delete=models.CASCADE, related_name='landmark_data')
    detected_landmark_name = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    formatted_address = models.CharField(max_length=255, blank=True, null=True)
    street_number = models.SmallIntegerField(null=True, blank=True)
    route = models.CharField(max_length=100, null=True, blank=True) 
    neighborhood = models.CharField(max_length=100, null=True, blank=True)
    sublocality = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    district = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    analysis_timestamp = models.DateTimeField(auto_now=True, help_text="When landmark analysis was last updated/completed")

    def __str__(self):
        return self.detected_landmark_name or f"Landmark data for Photo {self.photo.id}"
