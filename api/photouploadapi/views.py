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
import requests
from datetime import timedelta
from django.utils import timezone
import traceback


User = get_user_model()

PHOTOS_BUCKET_NAME = os.environ.get("PHOTOS_BUCKET_NAME", "your-gcs-photos-bucket-name")
VISION_API_KEY = os.environ.get("VISION_API_KEY")
GEOCODING_API_KEY = os.environ.get("GEOCODING_API_KEY")


# storage_client = storage.Client()
key_path = os.path.join(os.path.dirname(__file__), '../keys/photoupload-457815-a0b94f392541.json')
storage_client = storage.Client.from_service_account_json(key_path)

vision_client = vision.ImageAnnotatorClient()
gmaps_client = googlemaps.Client(key=GEOCODING_API_KEY)

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
        try:
            landmark = self._perform_photo_analysis(photo)
            landmark.save()
        except Exception as e:
            photo.processing_status = 'failed'
            photo.save()
            return Response({"error": "Photo analysis failed.", "details": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        photo.processing_status = 'completed'
        photo.save()            

        photo_response_serializer = PhotoSerializer(photo)
        landmark_serializer = LandmarkSerializer(landmark)
        return Response({
            "photo": photo_response_serializer.data,
            "landmark": landmark_serializer.data
        }, status=status.HTTP_201_CREATED)

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
        photo.processing_status = 'processing'
        photo.save()

        response_photo = self.sign_photo(photo)

        signed_url = response_photo.data.get("signed_url")

        try:
            url = f'https://vision.googleapis.com/v1/images:annotate?key={VISION_API_KEY}'

            data = {
            "requests": [
                {
                "image": {
                    "source": {
                    "imageUri": signed_url
                    }
                },
                "features": [
                    {
                    "type": "LANDMARK_DETECTION",
                    "maxResults": 1
                    }
                ]
                }
            ]
            }

            # Send the request
            response = requests.post(url, json=data)
            result = response.json()

            landmarks = result.get('responses', [])[0].get('landmarkAnnotations', [])

            if not landmarks or len(landmarks) == 0:
                photo.processing_status = 'completed'
                photo.save()
                #landmark = Landmark.objects.create(photo=photo, detected_landmark_name=str(response))
                landmark = Landmark.objects.create(photo=photo, detected_landmark_name="Unknown")
                return landmark

            landmark = landmarks[0]  # take the first landmark

            if "locations" not in landmark or len(landmark["locations"]) == 0:
                raise ValueError(f"Landmark {landmark['description']} has no coordinates.")

            lat_lng = landmark["locations"][0]["latLng"]
            
            latitude = lat_lng["latitude"]
            longitude = lat_lng["longitude"]
            
            try:
                reverse_geocode_result = self._reverse_geocode(latitude, longitude, GEOCODING_API_KEY)
                if not reverse_geocode_result:
                    raise ValueError("Reverse geocoding returned no results.")
                landmark = Landmark.objects.create(
                    photo=photo,
                    detected_landmark_name=landmark["description"],
                    latitude=latitude,
                    longitude=longitude,
                    formatted_address=reverse_geocode_result[0].get('formatted_address'),
                    street_number=self._extract_address_component(reverse_geocode_result[0].get('address_components', []), 'street_number'),
                    route=self._extract_address_component(reverse_geocode_result[0].get('address_components', []), 'route'),
                    neighborhood=self._extract_address_component(reverse_geocode_result[0].get('address_components', []), 'neighborhood'),
                    sublocality=self._extract_address_component(reverse_geocode_result[0].get('address_components', []), 'sublocality'),
                    state=self._extract_address_component(reverse_geocode_result[0].get('address_components', []), 'administrative_area_level_1'),
                    district=self._extract_address_component(reverse_geocode_result[0].get('address_components', []), 'administrative_area_level_2'),
                    country=self._extract_address_component(reverse_geocode_result[0].get('address_components', []), 'country'),
                    postal_code=self._extract_address_component(reverse_geocode_result[0].get('address_components', []), 'postal_code')
                )
                return landmark
            except Exception as e:
                photo.processing_status = 'failed'
                photo.save()
                raise Exception(f"Geocoding failed: {str(e)}")
        except Exception as e:
            photo.processing_status = 'failed'
            photo.save()
            raise e

    def _reverse_geocode(self, lat, lng, api_key):
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "latlng": f"{lat},{lng}",
            "key": api_key
        }
        response = requests.get(url, params=params)
        result = response.json()

        if response.status_code != 200 or result.get("status") != "OK":
            raise Exception(f"Geocoding API error: {result.get('error_message', result.get('status'))}")

        return result["results"]

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

    def sign_photo(self, photo):
        try:
            bucket = storage_client.bucket(PHOTOS_BUCKET_NAME)
            blob = bucket.blob(photo.gcs_blob_name)

            # Generate signed URL valid for 60 minutes
            url = blob.generate_signed_url(
                expiration=timedelta(minutes=60),
                method='GET',
                version='v4'
            )

            return Response({"signed_url": url})
        except Exception as e:
            print(traceback.format_exc())  # Or log to a logger
            return Response({"error": "Failed to generate signed URL.", "details": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @action(detail=True, methods=['get'], url_path='signed_url')
    def generate_signed_url(self, request, pk=None):
        """
        GET /api/v1/photos/{photo_id}/signed_url/
        Returns a temporary signed URL to access the photo.
        """
        photo = get_object_or_404(Photo, pk=pk, user=request.user)

        return self.sign_photo(photo)

        # try:
        #     bucket = storage_client.bucket(PHOTOS_BUCKET_NAME)
        #     blob = bucket.blob(photo.gcs_blob_name)
        #
        #     # Generate signed URL valid for 60 minutes
        #     url = blob.generate_signed_url(
        #         expiration=timedelta(minutes=60),
        #         method='GET',
        #         version='v4'
        #     )
        #
        #     return Response({"signed_url": url})
        # # except Exception as e:
        # #     return Response({"error": "Failed to generate signed URL.", "details": str(e)},
        # #                     status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # except Exception as e:
        #     print(traceback.format_exc())  # Or log to a logger
        #     return Response({"error": "Failed to generate signed URL.", "details": str(e)},
        #                     status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    
    serializer = PhotoSerializer(photos, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)