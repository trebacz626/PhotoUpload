# myapi/urls.py
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('hello/', views.hello, name='hello'),
    path('db_check/', views.db_check, name='db_check'),
    path('upload_photo/', views.upload_photo, name='upload_photo'),
    path('photo/<int:landmark_id>/', views.serve_photo, name='serve_photo'),
    path('photo/<int:landmark_id>/', views.delete_photo, name='delete_photo'),
    path('<int:landmark_id>/', views.trigger_analysis, name='trigger_analysis'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
