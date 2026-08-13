from django.db.models import Prefetch, Q
from django.shortcuts import render, get_object_or_404, redirect
from .models import BlogPost, BlogCategory
from media.models import BlogPostMedia
from django.contrib.auth.decorators import login_required
from .forms import BlogPostForm
from media.models import MediaAsset, BlogPostMedia


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

@login_required(login_url='login')
def post_create(request):

    if request.method == 'POST':

        form = BlogPostForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            post = form.save(
                commit=False
            )

            post.author_user = request.user

            post.status = "pending_review"

            post.save()


            cover_image = form.cleaned_data[
                'cover_image'
            ]

            cover_alt = (
                form.cleaned_data.get('cover_alt')
                or post.title
            )


            media_asset = MediaAsset.objects.create(

                uploaded_by=request.user,

                file=cover_image,

                original_name=cover_image.name,

                mime_type=getattr(
                    cover_image,
                    'content_type',
                    ''
                ),

                file_size=cover_image.size,

                media_type=MediaAsset.MediaType.IMAGE,

                title=post.title,

                alt_text=cover_alt,
            )


            BlogPostMedia.objects.create(

                post=post,

                media_asset=media_asset,

                purpose=BlogPostMedia.Purpose.COVER,

                alt_text=cover_alt,

                is_active=True,
            )


            return redirect(
                'blog:post_list'
            )

    else:

        form = BlogPostForm()


    return render(
        request,
        'blog/post_create.html',
        {'form': form}
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