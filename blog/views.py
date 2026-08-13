from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import BlogPost
from .services import publish_due_posts


def post_list(request):
    publish_due_posts()

    query = request.GET.get("q", "").strip()

    posts = (
        BlogPost.objects.filter(status="published")
        .select_related("author_user", "category")
        .order_by("-published_at", "-created_at")
    )

    if query:
        posts = posts.filter(
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(content__icontains=query)
            | Q(category__name__icontains=query)
            | Q(author_user__username__icontains=query)
        ).distinct()

    return render(
        request,
        "blog/post_list.html",
        {
            "posts": posts,
            "query": query,
        },
    )


def post_detail(request, slug):
    publish_due_posts()

    post = get_object_or_404(BlogPost,slug=slug,status="published",)
    cover = post.media_items.filter(purpose="cover",is_active=True,).select_related("media_asset").first()

    return render(request,"blog/post_detail.html",{ "post":post,"cover":cover,},)