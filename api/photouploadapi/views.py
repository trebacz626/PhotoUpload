import mimetypes
import os
from django.http import JsonResponse, HttpResponse, Http404
from django.db import connection
from api import settings
from .models import User, Landmark
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from .forms import ImageUploadForm
from django.views.decorators.csrf import csrf_exempt
from google.cloud import vision
import requests
from google.cloud import secretmanager
# from django.conf import settings
import io
from django.contrib.auth.decorators import login_required


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

@csrf_exempt
def upload_photo(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            landmark = form.save(commit=False)
            # Assign a dummy or default user
            try:
                # TODO user
                # user = request.user
                user = User.objects.first()  # one user needed
                if not user:
                    return JsonResponse({"status": "error", "message": "No user found in the database."}, status=500)
                landmark.user = user
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)

            landmark.save()
            return JsonResponse({
                "status": "ok",
                "message": "Image uploaded successfully.",
                "photo_url": landmark.photo_id.url
            })
    else:
        return JsonResponse({
            "status": "error",
            "message": "Only POST method is allowed."
        }, status=405)


def serve_photo(request, landmark_id):
    print(f"Serving landmark with ID: {landmark_id}")
    landmark = get_object_or_404(Landmark, landmark_id=landmark_id)
    photo_path = os.path.join(settings.MEDIA_ROOT, landmark.photo_id.name)

    if not os.path.exists(photo_path):
        return JsonResponse({"status": "error", "message": "File not found."}, status=404)

    # Get MIME type dynamically
    mime_type, _ = mimetypes.guess_type(photo_path)
    if not mime_type:
        mime_type = "application/octet-stream"  # Fallback for unknown types

    with open(photo_path, 'rb') as f:
        return HttpResponse(f.read(), content_type=mime_type)

# @login_required
@csrf_exempt
def delete_photo(request, landmark_id):
    # TODO does not work yet
    print(f"Deleting photo with ID: {landmark_id}")
    # Only allow DELETE method
    if request.method != 'DELETE':
        return JsonResponse({"status": "error", "message": "Method not allowed. Use DELETE."}, status=405)

    # Get the photo object (or return a 404 if not found)
    # landmark = get_object_or_404(Landmark, landmark_id=photo_id)
    landmark = Landmark.objects.get(id=landmark_id)

    # Get the full file path of the image
    photo_path = os.path.join(settings.MEDIA_ROOT, landmark.photo_id.name)

    # if landmark.photo_id:
    #     landmark.photo_id.delete()

    # Delete the photo from the database
    landmark.delete()
    print(landmark)
    print(Landmark.objects.get(id=landmark_id))

    # Delete the image file from the file system (if it exists)
    if os.path.exists(photo_path):
        os.remove(photo_path)

    return JsonResponse({"status": "ok", "message": "Photo deleted successfully."})


def detect_landmarks(path):
    """Detects the first landmark and returns its first coordinate."""
    client = vision.ImageAnnotatorClient()

    with open(path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.landmark_detection(image=image)

    if response.error.message:
        raise Exception(
            f"{response.error.message}\nFor more info on error messages, check: "
            "https://cloud.google.com/apis/design/errors"
        )

    landmarks = response.landmark_annotations
    if not landmarks:
        raise ValueError("No landmarks detected in the image.")

    landmark = landmarks[0]  # take the first landmark
    if not landmark.locations:
        raise ValueError(f"Landmark '{landmark.description}' has no coordinates.")

    lat_lng = landmark.locations[0].lat_lng
    return {
        "description": landmark.description,
        "location": {
            "latitude": lat_lng.latitude,
            "longitude": lat_lng.longitude
        }
    }


def get_geocoding_api_key():
    from google.cloud import secretmanager
    client = secretmanager.SecretManagerServiceClient()

    project_id = os.environ.get("GCP_PROJECT", "photoupload-457815")
    secret_name = f"{os.environ.get("APP_NAME", "landmark-app")}-geocoding-api-key"

    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"

    try:
        response = client.access_secret_version(request={"name": name})
        key = response.payload.data.decode("UTF-8")
        return key
    except Exception as e:
        print(f"Error accessing secret: {e}")
        return None

def reverse_geocode(lat, lng, api_key):
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


def trigger_analysis(request, landmark_id):
    try:
        # Get the corresponding landmark object
        landmark = Landmark.objects.get(landmark_id=landmark_id)
    except Landmark.DoesNotExist:
        raise Http404("No landmark found with that landmark_id.")

    # Build full path to the photo
    photo_path = os.path.join(settings.MEDIA_ROOT, landmark.photo_id.name)
    if not os.path.exists(photo_path):
        return JsonResponse({"status": "error", "message": "File not found."}, status=404)

    # Detect landmarks and extract coordinates
    response = {
        "status": None,
        "message": None,
        "latitude": None,
        "longitude": None,
        "geocoding_result": None
    }

    try:
        landmark_info = detect_landmarks(photo_path)
        landmark_location = landmark_info['location']
        lat = landmark_location["latitude"]
        lng = landmark_location["longitude"]

    # lat and lng not detected
    except ValueError as ve:
        # marking the image as processed (no additional info available)
        landmark.processed = True
        landmark.save()

        response["status"] = "success"
        response["message"] = str(ve)
        response["latitude"] = None
        response["longitude"] = None
        response["geocoding_result"] = None

        return JsonResponse(response)

    except Exception as e:
        return JsonResponse({
            "status": "detect landmark error",
            "message": str(e),
            "photo_path": photo_path
        })

    # Retrieve the Geocoding API key from Secret Manager
    try:
        api_key = get_geocoding_api_key()
    except Exception as e:
        return JsonResponse({
            "status": "secret access error",
            "message": str(e)
        })

    # Perform reverse geocoding
    try:
        res = reverse_geocode(lat, lng, api_key)
    except Exception as e:
        return JsonResponse({
            "status": "reverse geocoding error",
            "message": str(e)
        })

    # Update Landmark model fields
    landmark.latitude = lat
    landmark.longitude = lng

    if res:
        address = res[0]
        landmark.formatted_address = address.get("formatted_address")

        # Extract address components
        components = address.get("address_components", [])

        def get_component(short_type):
            for comp in components:
                if short_type in comp.get("types", []):
                    return comp.get("long_name")
            return None

        landmark.street_number = get_component("street_number")
        landmark.route = get_component("route")
        landmark.neighborhood = get_component("neighborhood")
        landmark.sublocality = get_component("sublocality")
        landmark.state = get_component("administrative_area_level_1")
        landmark.district = get_component("administrative_area_level_2")
        landmark.country = get_component("country")
        landmark.postal_code = get_component("postal_code")

        # Save the updated landmark
        landmark.processed = True
        landmark.save()

        response["status"] = "success"
        response["latitude"] = lat
        response["longitude"] = lng
        response["geocoding_result"] = res

    return JsonResponse(response)
