from django.http import JsonResponse
from django.db import connection
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Photo, Landmark
from .serializers import PhotoSerializer, PhotoUploadSerializer, LandmarkSerializer
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.conf import settings
import os
from google.cloud import storage, vision
import googlemaps 
import uuid

User = get_user_model()



PHOTOS_BUCKET_NAME = os.environ.get("PHOTOS_BUCKET_NAME", "your-gcs-photos-bucket-name")
# VISION_API_KEY = os.environ.get("VISION_API_KEY")
# GEOCODING_API_KEY = os.environ.get("GEOCODING_API_KEY")


storage_client = storage.Client()
# vision_client = vision.ImageAnnotatorClient()
# gmaps_client = googlemaps.Client(key=GEOCODING_API_KEY)

def db_check(request):
    try:
        user_exists = User.objects.exists()
        connected = True
        message = "Database connection successful and basic query executed."
    except Exception as e:
        connected = False
        message = f"Database connection failed: {e}"

    return JsonResponse({
        "status": "ok" if connected else "error",
        "message": message
    })

def hello(request):
    return JsonResponse({"message": "Hello from Django API!"})



class PhotoViewSet(viewsets.GenericViewSet):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_staff:
            return Photo.objects.filter(user=self.request.user).order_by('-upload_time')
        return super().get_queryset()

    @action(detail=False, methods=['post'], serializer_class=PhotoUploadSerializer, url_path='upload_photo')
    def upload_photo(self, request):
        """
        POST /api/v1/photos/upload_photo/
        Allows users to upload a photo. The request will contain an image file.
        The image is stored in Google Cloud Storage, and metadata in Cloud SQL.
        """
        serializer = PhotoUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        image_file = serializer.validated_data['image']
        original_filename = image_file.name
        
        gcs_blob_name = f"user_{request.user.id}/{uuid.uuid4()}_{original_filename}"

        try:
            bucket = storage_client.bucket(PHOTOS_BUCKET_NAME)
            blob = bucket.blob(gcs_blob_name)
            blob.upload_from_file(image_file.file, content_type=image_file.content_type)
        except Exception as e:
            return Response({"error": "Failed to upload image to GCS.", "details": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        photo = Photo.objects.create(
            user=request.user,
            gcs_blob_name=gcs_blob_name,
            original_filename=original_filename,
            processing_status='pending'
        )
        
        # self._perform_photo_analysis(photo)

        response_serializer = PhotoSerializer(photo)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def _extract_address_component(self, address_components, component_type):
        for component in address_components:
            if component_type in component.get('types', []):
                return component.get('long_name') or component.get('short_name')
        return None

    def _perform_photo_analysis(self, photo: Photo):
        """
        Internal method to perform landmark detection and geocoding.
        This simulates calls to Vision and Geocoding APIs.
        Ideally, this runs asynchronously.
        """
        # photo.processing_status = 'processing'
        # photo.save()
        
        #TODO call landmark api and detection api 
        raise NotImplementedError("Landmark detection API not implemented yet")


    @action(detail=True, methods=['post'], url_path='trigger_analysis')
    def trigger_analysis_for_photo(self, request, pk=None):
        """
        POST /api/v1/photos/{photo_id}/trigger_analysis/
        Triggers (or re-triggers) the landmark detection and geocoding process.
        """
        photo = get_object_or_404(Photo, pk=pk, user=request.user)

        if photo.processing_status == 'processing':
            return Response({'message': 'Analysis is already in progress.'}, status=status.HTTP_409_CONFLICT)

        self._perform_photo_analysis(photo)

        response_serializer = PhotoSerializer(photo)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='details', url_name='photo-detail')
    def retrieve_photo_details(self, request, pk=None):
        """
        GET /api/v1/photos/{photo_id}/details/
        Retrieves metadata for a specific photo, including landmark and geolocation if processed.
        """
        photo = get_object_or_404(Photo, pk=pk, user=request.user)
        serializer = PhotoSerializer(photo)
        return Response(serializer.data)

    @action(detail=True, methods=['delete'], url_path='delete')
    def delete_photo_by_id(self, request, pk=None):
        """
        DELETE /api/v1/photos/{photo_id}/delete/
        Deletes a specific photo (from GCS and Cloud SQL).
        """
        photo = get_object_or_404(Photo, pk=pk, user=request.user)

        try:
            bucket = storage_client.bucket(PHOTOS_BUCKET_NAME)
            blob = bucket.blob(photo.gcs_blob_name)
            if blob.exists():
               blob.delete()
        except Exception as e:
            print(f"Failed to delete GCS object {photo.gcs_blob_name}: {e}")
            return Response(
                {"error": "Failed to delete photo from Google Cloud Storage."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        photo.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_user_photos(request, user_id):
    """
    GET /api/v1/users/{user_id}/photos/
    Retrieves a list of all photos uploaded by a specific user.
    Basic metadata: photo IDs, upload times, processing statuses, original filename.
    """

    if request.user.id != user_id and not request.user.is_staff:
        return Response({"detail": "Not authorized to view these photos."}, status=status.HTTP_403_FORBIDDEN)

    target_user = get_object_or_404(User, pk=user_id)
    photos = Photo.objects.filter(user=target_user).order_by('-upload_time')
    
    basic_data = [{
        "photo_id": photo.id,
        "original_filename": photo.original_filename,
        "upload_time": photo.upload_time,
        "processing_status": photo.processing_status,
        "url": f"https://storage.googleapis.com/{PHOTOS_BUCKET_NAME}/{photo.gcs_blob_name}"
    } for photo in photos]
    
    return Response(basic_data)