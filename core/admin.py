from django.contrib import admin
from .models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = (
        'site_name',
        'posts_per_page',
        'registration_enabled',
        'comments_require_approval',
        'updated_at',
    )

    def has_add_permission(self, request):
        if SiteSettings.objects.exists():
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        return False