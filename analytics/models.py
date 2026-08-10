from django.db import models
from blog.models import BlogPost

class BlogPostDailyStat(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE)
    stat_date = models.DateField()
    views = models.PositiveIntegerField(default=0)
    reactions = models.PositiveIntegerField(default=0)
    comments = models.PositiveIntegerField(default=0)
    bookmarks = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)

    def __str__(self):
      return f'{self.post} - {self.stat_date}'