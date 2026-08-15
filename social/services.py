from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from blog.models import BlogPost

from .models import BlogBookmark, BlogComment, BlogContentReport, BlogReaction


COMMENT_EDIT_WINDOW_MINUTES = 15


def refresh_post_counters(post_id):
    """Recalculate social counters from source tables so counters never go negative/drift."""
    comment_count = BlogComment.objects.filter(
        post_id=post_id,
        status=BlogComment.Status.APPROVED,
    ).count()
    reaction_count = BlogReaction.objects.filter(post_id=post_id).count()
    bookmark_count = BlogBookmark.objects.filter(post_id=post_id).count()

    BlogPost.objects.filter(pk=post_id).update(
        comment_count=comment_count,
        reaction_count=reaction_count,
        bookmark_count=bookmark_count,
    )


@transaction.atomic
def create_comment(*, post, user, content, parent=None):
    if not post.allow_comments:
        raise ValidationError("Comments are closed for this post.")

    content = (content or "").strip()
    if not content:
        raise ValidationError("Comment content cannot be empty.")

    comment = BlogComment(
        post=post,
        user=user,
        parent=parent,
        content=content,
    )
    comment.full_clean()
    comment.save()

    # New comments are pending by default, therefore approved count usually stays unchanged.
    refresh_post_counters(post.pk)
    return comment


@transaction.atomic
def edit_comment(*, comment, user, content):
    if comment.user_id != user.pk:
        raise PermissionDenied("You can edit only your own comment.")

    deadline = comment.created_at + timedelta(minutes=COMMENT_EDIT_WINDOW_MINUTES)
    if timezone.now() > deadline:
        raise PermissionDenied("The comment edit window has expired.")

    if comment.status == BlogComment.Status.DELETED:
        raise ValidationError("A deleted comment cannot be edited.")

    content = (content or "").strip()
    if not content:
        raise ValidationError("Comment content cannot be empty.")

    comment.content = content
    comment.is_edited = True
    comment.full_clean()
    comment.save(update_fields=["content", "is_edited", "updated_at"])
    return comment


@transaction.atomic
def set_comment_status(*, comment, status):
    valid_statuses = {value for value, _ in BlogComment.Status.choices}
    if status not in valid_statuses:
        raise ValidationError("Invalid comment status.")

    comment.status = status
    comment.save(update_fields=["status", "updated_at"])
    refresh_post_counters(comment.post_id)
    return comment


@transaction.atomic
def toggle_reaction(*, post, user, reaction_type):
    valid_types = {value for value, _ in BlogReaction.ReactionType.choices}
    if reaction_type not in valid_types:
        raise ValidationError("Invalid reaction type.")

    reaction = (
        BlogReaction.objects.select_for_update()
        .filter(post=post, user=user)
        .first()
    )

    if reaction is None:
        reaction = BlogReaction.objects.create(
            post=post,
            user=user,
            reaction_type=reaction_type,
        )
        state = "created"
    elif reaction.reaction_type == reaction_type:
        reaction.delete()
        reaction = None
        state = "removed"
    else:
        reaction.reaction_type = reaction_type
        reaction.save(update_fields=["reaction_type"])
        state = "updated"

    refresh_post_counters(post.pk)
    post.refresh_from_db(fields=["reaction_count"])
    return state, reaction, post.reaction_count


@transaction.atomic
def toggle_bookmark(*, post, user):
    bookmark = (
        BlogBookmark.objects.select_for_update()
        .filter(post=post, user=user)
        .first()
    )

    if bookmark is None:
        bookmark = BlogBookmark.objects.create(post=post, user=user)
        state = "created"
    else:
        bookmark.delete()
        bookmark = None
        state = "removed"

    refresh_post_counters(post.pk)
    post.refresh_from_db(fields=["bookmark_count"])
    return state, bookmark, post.bookmark_count


@transaction.atomic
def create_report(
    *,
    reported_by,
    reason,
    description="",
    post=None,
    comment=None,
):
    has_post = post is not None
    has_comment = comment is not None

    if has_post == has_comment:
        raise ValidationError(
            "A report must target exactly one post or one comment."
        )

    valid_reasons = {
        value
        for value, _ in BlogContentReport.Reason.choices
    }

    if reason not in valid_reasons:
        raise ValidationError(
            "Invalid report reason."
        )

    # جلوگیری از Report تکراری روی Post
    if post is not None:
        duplicate_exists = BlogContentReport.objects.filter(
            reported_by=reported_by,
            post=post,
        ).exists()

        if duplicate_exists:
            raise ValidationError(
                "You have already reported this content."
            )

    # جلوگیری از Report تکراری روی Comment
    if comment is not None:
        duplicate_exists = BlogContentReport.objects.filter(
            reported_by=reported_by,
            comment=comment,
        ).exists()

        if duplicate_exists:
            raise ValidationError(
                "You have already reported this content."
            )

    report = BlogContentReport(
        reported_by=reported_by,
        post=post,
        comment=comment,
        reason=reason,
        description=(description or "").strip(),
    )

    report.full_clean()

    try:
        report.save()

    except IntegrityError as exc:
        raise ValidationError(
            "You have already reported this content."
        ) from exc

    return report

@transaction.atomic
def review_report(*, report, reviewer, status):
    valid_statuses = {
        BlogContentReport.Status.REVIEWED,
        BlogContentReport.Status.RESOLVED,
        BlogContentReport.Status.DISMISSED,
    }
    if status not in valid_statuses:
        raise ValidationError("Invalid review status.")

    report.status = status
    report.reviewed_by = reviewer
    report.reviewed_at = timezone.now()
    report.save(
        update_fields=["status", "reviewed_by", "reviewed_at", "updated_at"]
    )
    return report