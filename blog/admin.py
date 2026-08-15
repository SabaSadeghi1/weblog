from django.contrib import admin
from django import forms
from media.models import MediaAsset, BlogPostMedia
from .models import BlogCategory, BlogPost, BlogTag, BlogPostTag


class BlogPostAdminForm(forms.ModelForm):
    cover_image = forms.ImageField(required=False,label="Cover image")

    class Meta:
        model = BlogPost
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        cover_image = cleaned_data.get("cover_image")

        if self.instance.pk:
            has_cover = BlogPostMedia.objects.filter(
                post=self.instance,
                purpose="cover",
                is_active=True,
            ).exists()
        else:
            has_cover = False

        if not cover_image and not has_cover:
            self.add_error("cover_image","Cover image is required.")

        return cleaned_data
    
@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ("name","slug","is_active","created_at",)
    list_filter = ("is_active",)
    search_fields = ("name","slug",)
    readonly_fields = ("created_at","updated_at",)

@admin.register(BlogTag)
class BlogTagAdmin(admin.ModelAdmin):
    list_display = ("name","slug","is_active","created_at",)
    list_filter = ("is_active",)
    search_fields = ("name","slug",)
    readonly_fields = ("created_at","updated_at",)
    
class BlogPostTagInline(admin.TabularInline):
    model = BlogPostTag
    extra = 1

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    form = BlogPostAdminForm

    list_display = ("title","author_user","category","status","is_featured","scheduled_for","published_at",)
    list_filter = ("status","category","is_featured",)
    search_fields = ("title","slug","summary","content",)
    readonly_fields = ("slug","published_at","created_at","updated_at",)
    inlines = (BlogPostTagInline,)

    def save_model(self, request, obj, form, change):
        super().save_model(request,obj,form,change)

        cover_image = form.cleaned_data.get("cover_image")

        if cover_image:
            BlogPostMedia.objects.filter(
                post=obj,
                purpose="cover",
                is_active=True,
            ).update(is_active=False)

            media_asset = MediaAsset.objects.create(
                uploaded_by=request.user,
                file=cover_image,
                original_name=cover_image.name,
                mime_type=getattr(cover_image,"content_type",""),
                file_size=cover_image.size,
                media_type=MediaAsset.MediaType.IMAGE,
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
    list_display = ("post","tag",)
    search_fields = ("post__title","tag__name",)