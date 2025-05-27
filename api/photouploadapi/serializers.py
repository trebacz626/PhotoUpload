import os
from rest_framework import serializers
from .models import Photo, Landmark
from django.contrib.auth import get_user_model


PHOTOS_BUCKET_NAME = os.environ.get("PHOTOS_BUCKET_NAME", "your-gcs-photos-bucket-name")

User = get_user_model()

class LandmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Landmark
        fields = [
            'detected_landmark_name', 'latitude', 'longitude',
            'formatted_address', 'street_number', 'route', 'neighborhood',
            'sublocality', 'state', 'district', 'country', 'postal_code',
            'analysis_timestamp'
        ]

class PhotoSerializer(serializers.ModelSerializer):
    landmark_data = LandmarkSerializer(read_only=True, allow_null=True)
    user = serializers.ReadOnlyField(source='user.username')
    photo_id = serializers.IntegerField(source='id', read_only=True)
    gcs_url = serializers.SerializerMethodField()
    def get_gcs_url(self, obj):
        if obj.gcs_blob_name:
            return f"https://storage.googleapis.com/{PHOTOS_BUCKET_NAME}/{obj.gcs_blob_name}"
        return None


    class Meta:
        model = Photo
        fields = [
            'photo_id', 'user', 'gcs_blob_name', 'original_filename',
            'upload_time', 'processing_status', 'landmark_data', 'gcs_url'
        ]
        read_only_fields = ['upload_time', 'processing_status', 'user', 'gcs_blob_name']

class PhotoUploadSerializer(serializers.Serializer):
    image = serializers.ImageField(write_only=True, help_text="The photo file to upload.")