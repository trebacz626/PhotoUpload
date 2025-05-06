from django import forms
from .models import Landmark

class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = Landmark
        fields = ['photo_id']
