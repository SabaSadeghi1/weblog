from django.db.models import Prefetch, Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import BlogPost, BlogCategory
from .forms import BlogPostForm
from .services import publish_due_posts
from media.models import BlogPostMedia, MediaAsset
from django.db import transaction
from media.services import create_media_asset
from social.models import BlogBookmark, BlogComment, BlogContentReport, BlogReaction

def post_list(request):
    publish_due_posts()
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

@login_required(login_url="login")
@transaction.atomic
def post_create(request):
    if request.method == "POST":
        form = BlogPostForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            post = form.save(commit=False)

            post.author_user = request.user
            post.status = "pending_review"
            post.save()

            cover_image = form.cleaned_data["cover_image"]

            cover_alt = (
                form.cleaned_data.get("cover_alt")
                or post.title
            )

            cover_asset = create_media_asset(
                uploaded_file=cover_image,
                uploaded_by=request.user,
                title=post.title,
                alt_text=cover_alt,
            )

            BlogPostMedia.objects.create(
                post=post,
                media_asset=cover_asset,
                purpose=BlogPostMedia.Purpose.COVER,
                alt_text=cover_alt,
                is_active=True,
            )

            media_files = form.cleaned_data.get(
                "media_files",
                [],
            )

            for sort_order, uploaded_file in enumerate(
                media_files,
                start=1,
            ):
                media_asset = create_media_asset(
                    uploaded_file=uploaded_file,
                    uploaded_by=request.user,
                    title=uploaded_file.name,
                )

                if (
                    media_asset.media_type
                    == MediaAsset.MediaType.IMAGE
                ):
                    purpose = BlogPostMedia.Purpose.GALLERY
                else:
                    purpose = BlogPostMedia.Purpose.CONTENT

                BlogPostMedia.objects.create(
                    post=post,
                    media_asset=media_asset,
                    purpose=purpose,
                    sort_order=sort_order,
                    is_active=True,
                )

            return redirect("blog:post_list")

    else:
        form = BlogPostForm()

    return render(
        request,
        "blog/post_create.html",
        {"form": form},
    )



def post_detail(request, slug):
    publish_due_posts()

    post = get_object_or_404(
        BlogPost.objects
        .select_related("author_user", "category")
        .prefetch_related("tags"),
        slug=slug,
        status="published",
    )

    cover = (
        BlogPostMedia.objects.filter(
            post=post,
            purpose=BlogPostMedia.Purpose.COVER,
            is_active=True,
            media_asset__is_active=True,
        )
        .select_related("media_asset")
        .first()
    )

    content_media = (
        BlogPostMedia.objects.filter(
            post=post,
            purpose__in=[
                BlogPostMedia.Purpose.CONTENT,
                BlogPostMedia.Purpose.GALLERY,
            ],
            is_active=True,
            media_asset__is_active=True,
        )
        .select_related("media_asset")
        .order_by("sort_order", "created_at")
    )

    approved_replies = (
        BlogComment.objects.filter(status=BlogComment.Status.APPROVED)
        .select_related("user")
        .order_by("created_at")
    )

    comments = (
        BlogComment.objects.filter(
            post=post,
            parent__isnull=True,
            status=BlogComment.Status.APPROVED,
        )
        .select_related("user")
        .prefetch_related(
            Prefetch(
                "replies",
                queryset=approved_replies,
                to_attr="approved_replies",
            )
        )
        .order_by("created_at")
    )

    current_reaction = None
    is_bookmarked = False
    if request.user.is_authenticated:
        current_reaction = (
            BlogReaction.objects.filter(post=post, user=request.user)
            .values_list("reaction_type", flat=True)
            .first()
        )
        is_bookmarked = BlogBookmark.objects.filter(
            post=post,
            user=request.user,
        ).exists()

    return render(
        request,
        "blog/post_detail.html",
        {
            "post": post,
            "cover": cover,
            "content_media": content_media,
            "comments": comments,
            "current_reaction": current_reaction,
            "is_bookmarked": is_bookmarked,
            "reaction_choices": BlogReaction.ReactionType.choices,
            "report_reasons": BlogContentReport.Reason.choices,
        },
    )

