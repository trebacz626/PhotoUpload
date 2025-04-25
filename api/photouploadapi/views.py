from django.http import JsonResponse
from django.db import connection
from django.contrib.auth.models import User

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