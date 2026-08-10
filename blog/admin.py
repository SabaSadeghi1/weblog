from django.contrib import admin
from .models import BlogCategory, BlogPost, BlogTag, BlogPostTag

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
    list_display = ("title","author_user","category","status","is_featured","published_at",)
    list_filter = ("status","category","is_featured",)
    search_fields = ("title","slug","summary","content",)
    readonly_fields = ("created_at","updated_at",)
    inlines = (BlogPostTagInline,)

@admin.register(BlogPostTag)
class BlogPostTagAdmin(admin.ModelAdmin):
    list_display = ("post","tag",)
    search_fields = ("post__title","tag__name",)