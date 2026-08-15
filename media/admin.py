from django.contrib import admin
from django.utils.html import format_html

from .models import BlogPostMedia, MediaAsset


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = (
        "thumbnail",
        "original_name",
        "media_type",
        "uploaded_by",
        "file_size",
        "is_active",
        "created_at",
    )
    list_filter = ("media_type", "uploaded_by", "is_active", "created_at")
    search_fields = ("original_name", "title", "alt_text")
    readonly_fields = (
        "thumbnail",
        "original_name",
        "mime_type",
        "file_size",
        "width",
        "height",
        "duration",
        "created_at",
        "updated_at",
    )
    actions = ("activate_media", "soft_delete_media")

    @admin.display(description="Preview")
    def thumbnail(self, obj):
        if obj.media_type == MediaAsset.MediaType.IMAGE and obj.file:
            return format_html(
                '<img src="{}" width="70" height="50" '
                'style="object-fit: cover; border-radius: 4px;">',
                obj.file.url,
            )
        return "-"

    def has_delete_permission(self, request, obj=None):
        # Media is soft-deleted via is_active; disable accidental hard delete in admin.
        return False

    @admin.action(description="Activate selected media")
    def activate_media(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Soft-delete selected media")
    def soft_delete_media(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(BlogPostMedia)
class BlogPostMediaAdmin(admin.ModelAdmin):
    list_display = (
        "post",
        "media_asset",
        "purpose",
        "sort_order",
        "is_active",
        "created_at",
    )
    list_filter = ("purpose", "is_active", "created_at")
    search_fields = (
        "post__title",
        "media_asset__original_name",
        "media_asset__title",
    )
    autocomplete_fields = ("post", "media_asset")
    readonly_fields = ("created_at",)