from django.db import models
from django.conf import settings
from django.db.models import Q

class MediaAsset(models.Model):

    
    class MediaType(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"
        AUDIO = "audio", "Audio"
        DOCUMENT = "document", "Document"
        PDF = "pdf", "PDF"
        OTHER = "other", "Other"


    uploaded_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    null=True,
    related_name="uploaded_media_assets",
)
    file = models.FileField(
    upload_to="uploads/%Y/%m/",
    )


    original_name = models.CharField(
    max_length=255,
    editable=False,
    )

    mime_type = models.CharField(
        max_length=150,
        blank=True,
        editable=False,
    )

    file_size = models.PositiveBigIntegerField(
        default=0,
        editable=False,
    )

    width = models.PositiveIntegerField(
    null=True,
    blank=True,
    editable=False,
    )

    height = models.PositiveIntegerField(
    null=True,
    blank=True,
    editable=False,
    )

    duration = models.PositiveIntegerField(
    null=True,
    blank=True,
    editable=False,
    help_text="Duration in seconds",
    )

    title = models.CharField(
    max_length=200,
    blank=True,
    )

    alt_text = models.CharField(
        max_length=255,
        blank=True,
    )

    caption = models.TextField(
        blank=True,
    )

    is_active = models.BooleanField(
    default=True,
    db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )


    media_type = models.CharField(
        max_length=20,
        choices=MediaType.choices,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title or self.original_name or self.file.name




class BlogPostMedia(models.Model):
    class Purpose(models.TextChoices):
        COVER = "cover", "Cover"
        CONTENT = "content", "Content"
        GALLERY = "gallery", "Gallery"

    post = models.ForeignKey(
        "blog.BlogPost",
        on_delete=models.CASCADE,
        related_name="media_items",
    )

    media_asset = models.ForeignKey(
        MediaAsset,
        on_delete=models.PROTECT,
        related_name="post_placements",
    )

    purpose = models.CharField(
        max_length=20,
        choices=Purpose.choices,
    )

    caption = models.TextField(
        blank=True,
    )

    alt_text = models.CharField(
        max_length=255,
        blank=True,
    )

    sort_order = models.PositiveIntegerField(
        default=0,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["sort_order", "created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["post", "media_asset", "purpose"],
                name="unique_post_media_purpose",
            ),
            models.UniqueConstraint(
                fields=["post"],
                condition=Q(
                    purpose="cover",
                    is_active=True,
                ),
                name="unique_active_cover_per_post",
            ),
        ]

    def __str__(self):
        return f"{self.post_id} - {self.purpose} - {self.media_asset_id}"

    
    
