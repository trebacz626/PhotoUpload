import mimetypes
import os
from django.http import JsonResponse, HttpResponse
from django.db import connection
from api import settings
from .models import User, Landmark
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from .forms import ImageUploadForm
from django.views.decorators.csrf import csrf_exempt
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


def serve_photo(request, photo_id):
    print(f"Serving photo with ID: {photo_id}")
    landmark = get_object_or_404(Landmark, landmark_id=photo_id)
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
def delete_photo(request, photo_id):
    print(f"Deleting photo with ID: {photo_id}")
    # Only allow DELETE method
    if request.method != 'DELETE':
        return JsonResponse({"status": "error", "message": "Method not allowed. Use DELETE."}, status=405)

    # Get the photo object (or return a 404 if not found)
    # landmark = get_object_or_404(Landmark, landmark_id=photo_id)
    landmark = Landmark.objects.get(id=photo_id)

    # Get the full file path of the image
    photo_path = os.path.join(settings.MEDIA_ROOT, landmark.photo_id.name)

    # if landmark.photo_id:
    #     landmark.photo_id.delete()

    # Delete the photo from the database
    landmark.delete()
    print(landmark)
    print(Landmark.objects.get(id=photo_id))

    # Delete the image file from the file system (if it exists)
    if os.path.exists(photo_path):
        os.remove(photo_path)

    return JsonResponse({"status": "ok", "message": "Photo deleted successfully."})
