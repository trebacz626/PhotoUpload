# myapi/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('hello/', views.hello, name='hello'),
    path('db_check/', views.db_check, name='db_check'),
]