from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from analytics.models import BlogPostDailyStat
from blog.models import BlogPost
from social.models import BlogAuthorFollow


def trending_posts(request):

    start_date = (
        timezone.localdate()
        - timedelta(days=7)
    )

    stats = (
        BlogPostDailyStat.objects
        .filter(
            stat_date__gte=start_date,
            post__status='published'
        )
        .values(
            'post',
            'post__published_at'
        )
        .annotate(
            total_views=Sum('views'),
            total_reactions=Sum('reactions'),
            total_comments=Sum('comments'),
            total_bookmarks=Sum('bookmarks'),
            total_shares=Sum('shares'),
        )
    )

    result = []

    for stat in stats:

        published_at = stat[
            'post__published_at'
        ]

        if published_at:

            age_days = (
                timezone.now()
                - published_at
            ).days

        else:

            age_days = 7


        freshness_score = max(
            0,
            7 - age_days
        ) * 2


        score = (
            stat['total_views']
            + stat['total_reactions'] * 3
            + stat['total_comments'] * 4
            + stat['total_bookmarks'] * 2
            + stat['total_shares'] * 2
            + freshness_score
        )

        result.append(
            {
                'post_id': stat['post'],
                'score': score,
            }
        )

    result.sort(
        key=lambda item: item['score'],
        reverse=True
    )


    post_ids = [
        item['post_id']
        for item in result[:10]
    ]


    posts_dict = {
        post.id: post
        for post in BlogPost.objects.filter(
            id__in=post_ids,
            status='published',
            published_at__lte=timezone.now()
        )
    }


    posts = [
        posts_dict[post_id]
        for post_id in post_ids
        if post_id in posts_dict
    ]


    return render(
        request,
        'discovery/trending.html',
        {'posts': posts}
    )

@login_required(login_url='login')
def personalized_feed(request):

    followed_authors = (
        BlogAuthorFollow.objects
        .filter(
            follower_user=request.user
        )
        .values_list(
            'author_user_id',
            flat=True
        )
    )


    posts = (
        BlogPost.objects
        .filter(
            status='published',
            published_at__lte=timezone.now(),
            author_user_id__in=followed_authors
        )
        .select_related(
            'author_user',
            'category'
        )
        .order_by(
            '-published_at'
        )
    )


    if not posts.exists():

        posts = (
            BlogPost.objects
            .filter(
                status='published',
                published_at__lte=timezone.now()
            )
            .order_by(
                '-published_at'
            )[:10]
        )


    return render(
        request,
        'discovery/feed.html',
        {'posts': posts}
    )