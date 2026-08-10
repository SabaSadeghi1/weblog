from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class BlogComment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        SPAM = "spam", "Spam"
        DELETED = "deleted", "Deleted"

    post = models.ForeignKey(
        "blog.BlogPost",
        on_delete=models.CASCADE,
        related_name="comments",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blog_comments",
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
    )

    content = models.TextField(
        max_length=5000,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    is_edited = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["created_at"]

    def clean(self):
        super().clean()

        if self.parent_id:
            if self.parent.post_id != self.post_id:
                raise ValidationError(
                    {"parent": "Reply and parent comment must belong to the same post."}
                )

            if self.parent.parent_id:
                raise ValidationError(
                    {"parent": "Replies cannot be more than one level deep."}
                )

    def __str__(self):
        return f"Comment {self.pk} on post {self.post_id}"







class BlogReaction(models.Model):
    class ReactionType(models.TextChoices):
        LIKE = "like", "Like"
        LOVE = "love", "Love"
        USEFUL = "useful", "Useful"
        INTERESTING = "interesting", "Interesting"

    post = models.ForeignKey(
        "blog.BlogPost",
        on_delete=models.CASCADE,
        related_name="reactions",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blog_reactions",
    )

    reaction_type = models.CharField(
        max_length=20,
        choices=ReactionType.choices,
        default=ReactionType.LIKE,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["post", "user"],
                name="unique_reaction_per_post_user",
            ),
        ]

    def __str__(self):
        return f"{self.user_id} - {self.reaction_type} - {self.post_id}"




class BlogBookmark(models.Model):
    post = models.ForeignKey(
        "blog.BlogPost",
        on_delete=models.CASCADE,
        related_name="bookmarks",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blog_bookmarks",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["post", "user"],
                name="unique_bookmark_per_post_user",
            ),
        ]

    def __str__(self):
        return f"{self.user_id} bookmarked post {self.post_id}"




class BlogAuthorFollow(models.Model):
    follower_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following_authors",
    )

    author_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="author_followers",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["follower_user", "author_user"],
                name="unique_author_follow",
            ),
            models.CheckConstraint(
                condition=~models.Q(
                    follower_user=models.F("author_user"),
                ),
                name="prevent_self_follow",
            ),
        ]

    def clean(self):
        super().clean()

        if self.follower_user_id == self.author_user_id:
            raise ValidationError(
                {"author_user": "A user cannot follow themselves."}
            )

    def __str__(self):
        return f"{self.follower_user_id} follows {self.author_user_id}"



class BlogContentReport(models.Model):
    class Reason(models.TextChoices):
        SPAM = "spam", "Spam"
        HARASSMENT = "harassment", "Harassment"
        HATE_SPEECH = "hate_speech", "Hate Speech"
        MISINFORMATION = "misinformation", "Misinformation"
        COPYRIGHT = "copyright", "Copyright"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        REVIEWED = "reviewed", "Reviewed"
        RESOLVED = "resolved", "Resolved"
        DISMISSED = "dismissed", "Dismissed"

    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="content_reports",
    )

    post = models.ForeignKey(
        "blog.BlogPost",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="content_reports",
    )

    comment = models.ForeignKey(
        BlogComment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="content_reports",
    )

    reason = models.CharField(
        max_length=30,
        choices=Reason.choices,
    )

    description = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_content_reports",
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        editable=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.CheckConstraint(
                condition=(
                    (
                        models.Q(post__isnull=False)
                        & models.Q(comment__isnull=True)
                    )
                    |
                    (
                        models.Q(post__isnull=True)
                        & models.Q(comment__isnull=False)
                    )
                ),
                name="report_exactly_one_target",
            ),
            models.UniqueConstraint(
                fields=["reported_by", "post"],
                condition=models.Q(post__isnull=False),
                name="unique_reporter_post",
            ),
            models.UniqueConstraint(
                fields=["reported_by", "comment"],
                condition=models.Q(comment__isnull=False),
                name="unique_reporter_comment",
            ),
        ]

    def clean(self):
        super().clean()

        has_post = self.post_id is not None
        has_comment = self.comment_id is not None

        if has_post == has_comment:
            raise ValidationError(
                "A report must target exactly one post or one comment."
            )

    def __str__(self):
        target = (
            f"post {self.post_id}"
            if self.post_id
            else f"comment {self.comment_id}"
        )
        return f"Report by {self.reported_by_id} for {target}"
    
