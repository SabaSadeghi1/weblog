from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


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
        related_name="comments"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments"
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies"
    )

    content = models.TextField(
        max_length=5000
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )

    is_edited = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )


    class Meta:
        ordering = ["created_at"]


    def clean(self):


        if self.parent:

            if self.parent.post_id != self.post_id:
                raise ValidationError(
                    "Reply must belong to same post."
                )


            if self.parent.parent:
                raise ValidationError(
                    "Maximum comment depth is 2."
                )


    def __str__(self):
        return f"Comment {self.id}"




class BlogReaction(models.Model):

    class ReactionType(models.TextChoices):

        LIKE = "like","Like"
        LOVE = "love","Love"
        USEFUL = "useful","Useful"
        INTERESTING = "interesting","Interesting"



    post = models.ForeignKey(
        "blog.BlogPost",
        on_delete=models.CASCADE,
        related_name="reactions"
    )


    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reactions"
    )


    reaction_type = models.CharField(
        max_length=20,
        choices=ReactionType.choices,
        default=ReactionType.LIKE
    )


    created_at = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "post",
                    "user"
                ],
                name="unique_post_reaction"
            )

        ]



    def __str__(self):

        return f"{self.user} -> {self.post}"






class BlogBookmark(models.Model):


    post = models.ForeignKey(
        "blog.BlogPost",
        on_delete=models.CASCADE,
        related_name="bookmarks"
    )


    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookmarks"
    )


    created_at = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:

        constraints=[

            models.UniqueConstraint(
                fields=[
                    "post",
                    "user"
                ],
                name="unique_post_bookmark"
            )

        ]


    def __str__(self):

        return f"{self.user} saved {self.post}"






class BlogContentReport(models.Model):


    class Reason(models.TextChoices):

        SPAM="spam","Spam"
        HARASSMENT="harassment","Harassment"
        HATE="hate","Hate Speech"
        COPYRIGHT="copyright","Copyright"
        OTHER="other","Other"



    class Status(models.TextChoices):

        PENDING="pending","Pending"
        REVIEWED="reviewed","Reviewed"
        RESOLVED="resolved","Resolved"
        DISMISSED="dismissed","Dismissed"




    reported_by=models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports"
    )


    post=models.ForeignKey(
        "blog.BlogPost",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reports"
    )


    comment=models.ForeignKey(
        BlogComment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reports"
    )


    reason=models.CharField(
        max_length=30,
        choices=Reason.choices
    )


    description=models.TextField(
        blank=True
    )


    status=models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )


    reviewed_by=models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_reports"
    )


    reviewed_at=models.DateTimeField(
        null=True,
        blank=True
    )


    created_at=models.DateTimeField(
        auto_now_add=True
    )


    updated_at=models.DateTimeField(
        auto_now=True
    )



    class Meta:

        constraints=[

            models.CheckConstraint(
                condition=
                (
                    models.Q(post__isnull=False,
                             comment__isnull=True)
                    |
                    models.Q(post__isnull=True,
                             comment__isnull=False)
                ),
                name="one_report_target"
            )

        ]



    def clean(self):

        if bool(self.post)==bool(self.comment):

            raise ValidationError(
                "Report must target only post or comment."
            )



    def __str__(self):

        return f"Report {self.id}"
