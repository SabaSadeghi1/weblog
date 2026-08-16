from django.db import transaction
from django.db.models import Prefetch, Q
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import Http404, HttpResponseGone
from .models import BlogPost, BlogCategory
from .forms import BlogPostForm, BlogPostEditForm
from .services import publish_due_posts
from django.shortcuts import render, redirect, get_object_or_404
from media.models import MediaAsset, BlogPostMedia
from media.services import create_media_asset
from analytics.services import add_view
from blog.models import BlogSlugRedirect
from seo.models import GoneURL
from core.models import SiteSettings
from social.models import BlogBookmark, BlogComment, BlogContentReport, BlogReaction
from django.views.decorators.http import require_POST


def post_list(request):
    publish_due_posts()

    active_covers = BlogPostMedia.objects.filter(
        purpose=BlogPostMedia.Purpose.COVER,
        is_active=True,
    ).select_related("media_asset")

    posts = (
        BlogPost.objects.filter(
            status="published",
            published_at__lte=timezone.now(),
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

    q = request.GET.get("q", "")
    category_slug = request.GET.get("category", "")
    tag_slug = request.GET.get("tag", "")
    author = request.GET.get("author", "")
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")
    ordering = request.GET.get("ordering", "newest")

    if tag_slug:
        posts = posts.filter(tags__slug=tag_slug)

    if author:
        posts = posts.filter(author_user__username=author)

    if date_from:
        posts = posts.filter(published_at__date__gte=date_from)

    if date_to:
        posts = posts.filter(published_at__date__lte=date_to)

    if ordering == "oldest":
        posts = posts.order_by("published_at")
    else:
        posts = posts.order_by("-published_at")

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
        posts = posts.filter(category__slug=category_slug)

    categories = BlogCategory.objects.filter(is_active=True)

    site_settings = SiteSettings.objects.filter(singleton_key="global").first()
    posts_per_page = site_settings.posts_per_page if site_settings else 9

    paginator = Paginator(posts, posts_per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "posts": page_obj,
        "page_obj": page_obj,
        "categories": categories,
        "q": q,
        "selected_category": category_slug,
        "selected_tag": tag_slug,
        "selected_author": author,
        "date_from": date_from,
        "date_to": date_to,
        "ordering": ordering,
    }

    return render(request, "blog/post_list.html", context)


@login_required(login_url="login")
@permission_required("blog.add_blogpost", raise_exception=True)
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

        
            post.seo_title = post.title
            post.seo_description = post.summary

            post.save()

            cover_image = form.cleaned_data["cover_image"]
            cover_alt = post.title

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

            media_files = form.cleaned_data.get("media_files", [])

            for sort_order, uploaded_file in enumerate(media_files, start=1):
                media_asset = create_media_asset(
                    uploaded_file=uploaded_file,
                    uploaded_by=request.user,
                    title=uploaded_file.name,
                )

                if media_asset.media_type == MediaAsset.MediaType.IMAGE:
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

@login_required(login_url="login")
@permission_required("blog.change_blogpost", raise_exception=True)
@transaction.atomic
def post_edit(request, slug):

    post = get_object_or_404(
        BlogPost,
        slug=slug,
        author_user=request.user,
    )

    if request.method == "POST":

        form = BlogPostEditForm(
            request.POST,
            instance=post,
        )

        if form.is_valid():

            post = form.save(commit=False)

            # Because the author changed the post,
            # send it for review again
            post.status = "pending_review"

            # Default SEO values
            post.seo_title = post.title
            post.seo_description = post.summary

            post.save()

            return redirect("profile")

    else:

        form = BlogPostEditForm(
            instance=post,
        )

    return render(
        request,
        "blog/post_edit.html",
        {
            "form": form,
            "post": post,
        },
    )

@login_required(login_url="login")
@permission_required("blog.delete_blogpost", raise_exception=True)
@require_POST
def post_delete(request, slug):

    post = get_object_or_404(
        BlogPost,
        slug=slug,
        author_user=request.user,
    )

    post.delete()

    return redirect("profile")

def post_detail(request, slug):
    publish_due_posts()

    gone = GoneURL.objects.filter(
        path=request.path,
        is_active=True,
    ).exists()

    if gone:
        return HttpResponseGone("This page has been permanently removed.")

    try:
        visibility_filter = Q(
            status="published",
            published_at__lte=timezone.now(),
        )

        if request.user.is_authenticated:
            visibility_filter |= Q(author_user=request.user)

        post = (
            BlogPost.objects
            .select_related("author_user", "category")
            .prefetch_related("tags")
            .get(
                visibility_filter,
                slug=slug,
            )
        )
    except BlogPost.DoesNotExist:
        old_slug = (
            BlogSlugRedirect.objects
            .select_related("post")
            .filter(
                old_slug=slug,
                post__status="published",
                post__published_at__lte=timezone.now(),
            )
            .first()
        )

        if old_slug:
            return redirect(
                old_slug.post.get_absolute_url(),
                permanent=True,
            )

        raise Http404

    cover = (
        BlogPostMedia.objects
        .filter(
            post=post,
            purpose=BlogPostMedia.Purpose.COVER,
            is_active=True,
            media_asset__is_active=True,
        )
        .select_related("media_asset")
        .first()
    )

    content_media = (
        BlogPostMedia.objects
        .filter(
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

    view_key = f"post_view_{post.id}_{timezone.localdate()}"

    if not request.session.get(view_key):
        add_view(post)
        request.session[view_key] = True

    post_tags = post.tags.all()

    related_posts = (
        BlogPost.objects
        .filter(
            status="published",
            published_at__lte=timezone.now(),
        )
        .exclude(id=post.id)
        .filter(
            Q(category=post.category)
            | Q(tags__in=post_tags)
        )
        .distinct()
        .order_by("-published_at")[:4]
    )

    approved_replies = (
        BlogComment.objects
        .filter(status=BlogComment.Status.APPROVED)
        .select_related("user")
        .order_by("created_at")
    )

    comments = (
        BlogComment.objects
        .filter(
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
            BlogReaction.objects
            .filter(post=post, user=request.user)
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
            "related_posts": related_posts,
        },
    )