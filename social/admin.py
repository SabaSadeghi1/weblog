
from django.contrib import admin
from django.utils import timezone

from .models import (
    BlogAuthorFollow,
    BlogBookmark,
    BlogComment,
    BlogContentReport,
    BlogReaction,
)


@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ("post", "user", "status", "is_edited", "created_at")
    list_filter = ("status", "post", "user", "created_at")
    search_fields = ("content", "post__title", "user__username")
    readonly_fields = ("created_at", "updated_at")
    actions = (
        "approve_comments",
        "reject_comments",
        "mark_as_spam",
        "soft_delete_comments",
    )

    @admin.action(description="Approve selected comments")
    def approve_comments(self, request, queryset):
        queryset.update(status=BlogComment.Status.APPROVED)

    @admin.action(description="Reject selected comments")
    def reject_comments(self, request, queryset):
        queryset.update(status=BlogComment.Status.REJECTED)

    @admin.action(description="Mark selected comments as spam")
    def mark_as_spam(self, request, queryset):
        queryset.update(status=BlogComment.Status.SPAM)

    @admin.action(description="Soft-delete selected comments")
    def soft_delete_comments(self, request, queryset):
        queryset.update(status=BlogComment.Status.DELETED)


@admin.register(BlogReaction)
class BlogReactionAdmin(admin.ModelAdmin):
    list_display = ("post", "user", "reaction_type", "created_at")
    list_filter = ("reaction_type", "created_at")
    search_fields = ("post__title", "user__username")
    readonly_fields = ("created_at",)


@admin.register(BlogBookmark)
class BlogBookmarkAdmin(admin.ModelAdmin):
    list_display = ("post", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("post__title", "user__username")
    readonly_fields = ("created_at",)


@admin.register(BlogAuthorFollow)
class BlogAuthorFollowAdmin(admin.ModelAdmin):
    list_display = ("follower_user", "author_user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("follower_user__username", "author_user__username")
    readonly_fields = ("created_at",)


@admin.register(BlogContentReport)
class BlogContentReportAdmin(admin.ModelAdmin):
    list_display = (
        "reported_by",
        "post",
        "comment",
        "reason",
        "status",
        "reviewed_by",
        "created_at",
    )
    list_filter = ("reason", "status", "created_at")
    search_fields = (
        "reported_by__username",
        "post__title",
        "comment__content",
        "description",
    )
    readonly_fields = ("reviewed_at", "created_at", "updated_at")
    actions = ("mark_as_reviewed", "mark_as_resolved", "dismiss_reports")

    def set_report_status(self, request, queryset, status):
        queryset.update(
            status=status,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )

    @admin.action(description="Mark selected reports as reviewed")
    def mark_as_reviewed(self, request, queryset):
        self.set_report_status(
            request,
            queryset,
            BlogContentReport.Status.REVIEWED,
        )

    @admin.action(description="Resolve selected reports")
    def mark_as_resolved(self, request, queryset):
        self.set_report_status(
            request,
            queryset,
            BlogContentReport.Status.RESOLVED,
        )

    @admin.action(description="Dismiss selected reports")
    def dismiss_reports(self, request, queryset):
        self.set_report_status(
            request,
            queryset,
            BlogContentReport.Status.DISMISSED,
        )
