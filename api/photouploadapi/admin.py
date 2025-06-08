from django.contrib import admin
from .models import Photo, Landmark

class LandmarkInline(admin.StackedInline):
    model = Landmark
    extra = 0 
    readonly_fields = ('analysis_timestamp',) 
    fieldsets = (
        (None, {
            'fields': ('detected_landmark_name', 'latitude', 'longitude', 'formatted_address')
        }),
        ('Address Components', {
            'classes': ('collapse',),
            'fields': (
                'street_number', 'route', 'neighborhood', 'sublocality', 
                'state', 'district', 'country', 'postal_code'
            )
        }),
        ('Metadata', {
            'fields': ('analysis_timestamp',)
        })
    )

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'original_filename', 'upload_time', 'processing_status', 'gcs_blob_name')
    list_filter = ('processing_status', 'user', 'upload_time')
    search_fields = ('original_filename', 'user__username', 'gcs_blob_name')
    inlines = [LandmarkInline]
    readonly_fields = ('upload_time',)
    actions = ['reprocess_photos']

    def reprocess_photos(self, request, queryset):
        from .views import PhotoViewSet
        analyzer = PhotoViewSet()
        count = 0
        for photo in queryset:
            if photo.processing_status != 'processing':
                try:
                    analyzer._perform_photo_analysis(photo)
                    count += 1
                except Exception as e:
                    self.message_user(request, f"Error reprocessing {photo.original_filename}: {e}", level='error')
        self.message_user(request, f"Successfully started reprocessing for {count} photos.")
    reprocess_photos.short_description = "Re-trigger landmark analysis for selected photos"


@admin.register(Landmark)
class LandmarkAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_photo_id', 'get_photo_user', 'detected_landmark_name', 'country', 'state', 'analysis_timestamp')
    list_filter = ('country', 'state', 'analysis_timestamp')
    search_fields = ('detected_landmark_name', 'photo__original_filename', 'photo__user__username', 'country', 'state', 'postal_code')
    raw_id_fields = ('photo',) 
    readonly_fields = ('analysis_timestamp',)
    fieldsets = (
        (None, {
            'fields': ('photo', 'detected_landmark_name', 'latitude', 'longitude', 'formatted_address')
        }),
        ('Detailed Address Components', {
            'classes': ('collapse',),
            'fields': (
                'street_number', 'route', 'neighborhood', 'sublocality', 
                'state', 'district', 'country', 'postal_code'
            )
        }),
        ('Metadata', {
            'fields': ('analysis_timestamp',)
        })
    )

    def get_photo_id(self, obj):
        return obj.photo.id
    get_photo_id.admin_order_field = 'photo'
    get_photo_id.short_description = 'Photo ID'

    def get_photo_user(self, obj):
        return obj.photo.user.username
    get_photo_user.admin_order_field = 'photo__user'
    get_photo_user.short_description = 'Uploaded by'