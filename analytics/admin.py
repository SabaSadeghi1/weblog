from django.contrib import admin
from .models import BlogPostDailyStat


@admin.register(BlogPostDailyStat)
class BlogPostDailyStatAdmin(admin.ModelAdmin):
    list_display = (
        'post',
        'stat_date',
        'views',
        'unique_views',
        'reactions',
        'comments',
        'bookmarks',
        'shares',
    )

    list_filter = (
        'stat_date',
    )

    search_fields = (
        'post__title',
    )