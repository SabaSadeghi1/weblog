from django import forms
from django.contrib import admin
from django.db import transaction

from media.models import BlogPostMedia
from media.services import create_media_asset

from .models import BlogCategory, BlogPost, BlogPostTag, BlogTag



class BlogPostAdminForm(forms.ModelForm):
    cover_image = forms.ImageField(required=False, label="Cover image")

    class Meta:
        model = BlogPost
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        cover_image = cleaned_data.get("cover_image")

        has_cover = False
        if self.instance.pk:
            has_cover = BlogPostMedia.objects.filter(
                post=self.instance,
                purpose=BlogPostMedia.Purpose.COVER,
                is_active=True,
            ).exists()

        if not cover_image and not has_cover:
            self.add_error("cover_image", "Cover image is required.")

        return cleaned_data


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    readonly_fields = ("created_at", "updated_at")


@admin.register(BlogTag)
class BlogTagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    readonly_fields = ("created_at", "updated_at")


class BlogPostTagInline(admin.TabularInline):
    model = BlogPostTag
    extra = 1


class BlogPostMediaInline(admin.TabularInline):
    model = BlogPostMedia
    extra = 0
    autocomplete_fields = ("media_asset",)
    fields = ("media_asset", "purpose", "caption", "alt_text", "sort_order", "is_active")


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    form = BlogPostAdminForm
    list_display = (
        "title",
        "author_user",
        "category",
        "status",
        "is_featured",
        "allow_comments",
        "comment_count",
        "reaction_count",
        "bookmark_count",
        "scheduled_for",
        "published_at",
    )
    list_filter = ("status", "category", "is_featured", "allow_comments")
    search_fields = ("title", "slug", "summary", "content")
    readonly_fields = (
        "slug",
        "published_at",
        "comment_count",
        "reaction_count",
        "bookmark_count",
        "created_at",
        "updated_at",
    )
    inlines = (BlogPostTagInline, BlogPostMediaInline)
    actions = ["approve_posts","reject_posts","publish_posts","archive_posts"]
    def approve_posts(self,request,queryset):
        for post in queryset:
            if post.status == "pending_review":
                post.status = "approved"
                post.save()


    def reject_posts(self,request,queryset):
        for post in queryset:
            if post.status == "pending_review":
                post.status = "rejected"
                post.save()


    def publish_posts(self,request,queryset):
        for post in queryset:
            if post.status == "approved":
                post.status = "published"
                post.save()


    def archive_posts(self,request,queryset):
        for post in queryset:
            if post.status == "published":
                post.status = "archived"
                post.save()
    @transaction.atomic
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        cover_image = form.cleaned_data.get("cover_image")
        if not cover_image:
            return

        BlogPostMedia.objects.filter(
            post=obj,
            purpose=BlogPostMedia.Purpose.COVER,
            is_active=True,
        ).update(is_active=False)

        media_asset = create_media_asset(
            uploaded_file=cover_image,
            uploaded_by=request.user,
            title=obj.title,
            alt_text=obj.title,
        )

        BlogPostMedia.objects.create(
            post=obj,
            media_asset=media_asset,
            purpose=BlogPostMedia.Purpose.COVER,
            alt_text=obj.title,
            is_active=True,
        )


@admin.register(BlogPostTag)
class BlogPostTagAdmin(admin.ModelAdmin):
    list_display = ("post", "tag")
    search_fields = ("post__title", "tag__name")