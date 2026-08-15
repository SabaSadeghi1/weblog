from django.contrib import admin
from django.utils.html import format_html

from .models import BlogBookmark, BlogComment, BlogContentReport, BlogReaction
from .services import review_report, set_comment_status


STATUS_COLORS = {
    "pending": "#b7791f",
    "approved": "#2f855a",
    "reviewed": "#2b6cb0",
    "resolved": "#2f855a",
    "rejected": "#c53030",
    "spam": "#805ad5",
    "deleted": "#718096",
    "dismissed": "#718096",
}


def _badge(value):
    color = STATUS_COLORS.get(value, "#4a5568")
    return format_html(
        '<span style="padding:3px 8px;border-radius:999px;background:{};color:white;font-weight:600;">{}</span>',
        color,
        value,
    )


@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ("post", "user", "status_badge", "is_edited", "created_at")
    list_filter = ("status", "post", "user", "created_at")
    search_fields = ("content", "post__title", "user__username")
    readonly_fields = ("created_at", "updated_at")
    actions = (
        "approve_comments",
        "reject_comments",
        "mark_as_spam",
        "soft_delete_comments",
    )

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        return _badge(obj.status)

    def _set_status(self, queryset, status):
        for comment in queryset.select_related("post"):
            set_comment_status(comment=comment, status=status)

    @admin.action(description="Approve selected comments")
    def approve_comments(self, request, queryset):
        self._set_status(queryset, BlogComment.Status.APPROVED)

    @admin.action(description="Reject selected comments")
    def reject_comments(self, request, queryset):
        self._set_status(queryset, BlogComment.Status.REJECTED)

    @admin.action(description="Mark selected comments as spam")
    def mark_as_spam(self, request, queryset):
        self._set_status(queryset, BlogComment.Status.SPAM)

    @admin.action(description="Soft-delete selected comments")
    def soft_delete_comments(self, request, queryset):
        self._set_status(queryset, BlogComment.Status.DELETED)


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


@admin.register(BlogContentReport)
class BlogContentReportAdmin(admin.ModelAdmin):
    list_display = (
        "reported_by",
        "post",
        "comment",
        "reason",
        "status_badge",
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
    actions = ("mark_as_reviewed", "mark_as_resolved", "dismiss_reports", "hide_reported_content")

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        return _badge(obj.status)

    def _set_report_status(self, request, queryset, status):
        for report in queryset.select_related("post", "comment"):
            review_report(report=report, reviewer=request.user, status=status)

    @admin.action(description="Mark selected reports as reviewed")
    def mark_as_reviewed(self, request, queryset):
        self._set_report_status(request, queryset, BlogContentReport.Status.REVIEWED)

    @admin.action(description="Resolve selected reports")
    def mark_as_resolved(self, request, queryset):
        self._set_report_status(request, queryset, BlogContentReport.Status.RESOLVED)

    @admin.action(description="Dismiss selected reports")
    def dismiss_reports(self, request, queryset):
        self._set_report_status(request, queryset, BlogContentReport.Status.DISMISSED)

    @admin.action(description="Hide reported content and resolve")
    def hide_reported_content(self, request, queryset):
        for report in queryset.select_related("post", "comment"):
            if report.comment_id:
                set_comment_status(
                    comment=report.comment,
                    status=BlogComment.Status.DELETED,
                )
            elif report.post_id:
                report.post.status = "rejected"
                report.post.save()

            review_report(
                report=report,
                reviewer=request.user,
                status=BlogContentReport.Status.RESOLVED,
            )