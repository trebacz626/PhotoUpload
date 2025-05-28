# myapi/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PhotoViewSet, list_user_photos, hello, db_check

router = DefaultRouter()
router.register(r'photos', PhotoViewSet, basename='photo')


urlpatterns = [
    path('hello/', hello, name='hello'),
    path('db_check/', db_check, name='db_check'),
    path('', include(router.urls)),
    path('users/<int:user_id>/photos/', list_user_photos, name='user-photos-list'),
]