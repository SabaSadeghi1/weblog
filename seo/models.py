from django.db import models


class GoneURL(models.Model):

    path = models.CharField(
        max_length=500,
        unique=True
    )

    reason = models.CharField(
        max_length=250,
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )


    def __str__(self):
        return self.path