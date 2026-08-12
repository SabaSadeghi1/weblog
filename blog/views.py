from django.shortcuts import get_object_or_404, render
from .models import BlogPost
from .services import publish_due_posts


def post_list(request):
    publish_due_posts()

    posts = BlogPost.objects.filter(status="published")
    return render(request, "blog/post_list.html", {"posts":posts})

def post_detail(request, slug):
    publish_due_posts()

    post = get_object_or_404(BlogPost,slug=slug,status="published",)
    cover = post.media_items.filter(purpose="cover",is_active=True,).select_related("media_asset").first()

    return render(request,"blog/post_detail.html",{ "post":post,"cover":cover,},)