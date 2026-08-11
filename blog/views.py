from django.shortcuts import get_object_or_404, render
from .models import BlogPost

def post_list(request):
    posts = BlogPost.objects.all()
    return render(request, "blog/post_list.html", {"posts":posts})

def post_detail(request, slug):
    post = get_object_or_404(
        BlogPost,
        slug=slug,
        status="published",
    )
    return render(request, "blog/post_detail.html", {"post":post})