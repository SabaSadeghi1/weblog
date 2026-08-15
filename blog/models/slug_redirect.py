from django.db import models

from .post import BlogPost


class BlogSlugRedirect(models.Model):

    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name='slug_redirects'
    )

    old_slug = models.SlugField(
        max_length=270,
        unique=True,
        allow_unicode=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.old_slug