from django.utils import timezone
from .models import BlogPost


def publish_due_posts():
    posts = BlogPost.objects.filter(
        status="scheduled",
        scheduled_for__lte=timezone.now(),
    )

    for post in posts:
        post.status = "published"
        post.save()