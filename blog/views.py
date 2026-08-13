from django.db.models import Prefetch, Q
from django.shortcuts import render, get_object_or_404
from .models import BlogPost, BlogCategory
from media.models import BlogPostMedia


def post_list(request):

    active_covers = BlogPostMedia.objects.filter(
        purpose=BlogPostMedia.Purpose.COVER,
        is_active=True,
    ).select_related("media_asset")


    posts = (
        BlogPost.objects.filter(status="published")
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


    q = request.GET.get("q", "")

    category_slug = request.GET.get("category", "")


    if q:

        posts = posts.filter(

            Q(title__icontains=q)
            | Q(summary__icontains=q)
            | Q(content__icontains=q)
            | Q(category__name__icontains=q)
            | Q(tags__name__icontains=q)
            | Q(author_user__username__icontains=q)

        ).distinct()


    if category_slug:

        posts = posts.filter(
            category__slug=category_slug
        )


    categories = BlogCategory.objects.filter(
        is_active=True
    )


    context = {
        "posts": posts,
        "categories": categories,
        "q": q,
        "selected_category": category_slug,
    }


    return render(
        request,
        "blog/post_list.html",
        context
    )

def post_detail(request, slug):

    post = get_object_or_404(
        BlogPost,
        slug=slug
    )

    return render(
        request,
        "blog/post_detail.html",
        {"post": post}
    )