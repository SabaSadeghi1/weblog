from django.db.models import Count, Prefetch, Q
from django.shortcuts import render
from django.utils import timezone
from blog.models import BlogCategory, BlogPost
from media.models import BlogPostMedia


def landing_page(request):
    active_covers = BlogPostMedia.objects.filter(
        purpose=BlogPostMedia.Purpose.COVER,
        is_active=True,
    ).select_related("media_asset")

    published_posts = (
        BlogPost.objects.filter(
            status="published",
            published_at__lte=timezone.now()
        )
        .select_related("author_user", "category")
        .prefetch_related(
            Prefetch(
                "media_items",
                queryset=active_covers,
                to_attr="active_covers",
            )
        )
        .order_by("-published_at", "-created_at")
    )

    featured_post = published_posts.filter(
        is_featured=True
    ).first()

    if featured_post is None:
        featured_post = published_posts.first()

    if featured_post:
        latest_posts = published_posts.exclude(
            pk=featured_post.pk
        )[:6]
    else:
        latest_posts = published_posts[:6]

    categories = (
        BlogCategory.objects.filter(is_active=True)
        .annotate(
            published_post_count=Count(
                "posts",
                filter=Q(
                posts__status="published",
                posts__published_at__lte=timezone.now()
            )
            )
        )
        .filter(published_post_count__gt=0)
        .order_by("-published_post_count", "name")[:6]
    )

    context = {
        "featured_post": featured_post,
        "latest_posts": latest_posts,
        "categories": categories,
    }

    return render(request, "core/landing.html", context)