from django.db.models import F
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from .models import BlogPostDailyStat
from django.db import transaction


@transaction.atomic
def add_view(post):

    stat, created = BlogPostDailyStat.objects.get_or_create(
        post=post,
        stat_date=timezone.localdate()
    )

    BlogPostDailyStat.objects.filter(
        id=stat.id
    ).update(
        views=F('views') + 1
    )


def author_stats(user, days=7):

    start_date = (
        timezone.localdate()
        - timedelta(days=days)
    )

    return (
        BlogPostDailyStat.objects
        .filter(
            post__author_user=user,
            stat_date__gte=start_date
        )
        .aggregate(
            views=Sum('views'),
            reactions=Sum('reactions'),
            comments=Sum('comments'),
            bookmarks=Sum('bookmarks'),
            shares=Sum('shares'),
        )
    )