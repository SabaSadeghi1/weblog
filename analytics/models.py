from django.db import models


class BlogPostDailyStat(models.Model):
    post = models.ForeignKey(
        'blog.BlogPost',
        on_delete=models.CASCADE,
        related_name='daily_stats'
    )

    stat_date = models.DateField()

    views = models.PositiveIntegerField(default=0)
    unique_views = models.PositiveIntegerField(default=0)

    reactions = models.PositiveIntegerField(default=0)
    comments = models.PositiveIntegerField(default=0)
    bookmarks = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['post', 'stat_date'],
                name='unique_post_daily_stat'
            )
        ]

    def __str__(self):
        return f'{self.post} - {self.stat_date}'