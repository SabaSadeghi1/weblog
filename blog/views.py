from django.db.models import Prefetch, Q
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import Http404, HttpResponseGone

from .models import BlogPost, BlogCategory
from .forms import BlogPostForm
from .services import publish_due_posts

from media.models import MediaAsset, BlogPostMedia
from analytics.services import add_view
from blog.models import BlogSlugRedirect
from seo.models import GoneURL
from core.models import SiteSettings


def post_list(request):
    publish_due_posts()
    active_covers = BlogPostMedia.objects.filter(
        purpose=BlogPostMedia.Purpose.COVER,
        is_active=True,
    ).select_related("media_asset")


    posts = (
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


    q = request.GET.get("q", "")

    category_slug = request.GET.get("category", "")

    tag_slug = request.GET.get(
        'tag',
        ''
    )

    author = request.GET.get(
        'author',
        ''
    )

    date_from = request.GET.get(
        'date_from',
        ''
    )

    date_to = request.GET.get(
        'date_to',
        ''
    )

    ordering = request.GET.get(
        'ordering',
        'newest'
    )

    if tag_slug:

        posts = posts.filter(
            tags__slug=tag_slug
        )


    if author:

        posts = posts.filter(
            author_user__username=author
        )


    if date_from:

        posts = posts.filter(
            published_at__date__gte=date_from
        )


    if date_to:

        posts = posts.filter(
            published_at__date__lte=date_to
        )


    if ordering == 'oldest':

        posts = posts.order_by(
            'published_at'
        )

    else:

        posts = posts.order_by(
            '-published_at'
        )
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
    site_settings = SiteSettings.objects.filter(
        singleton_key='global'
    ).first()


    if site_settings:

        posts_per_page = site_settings.posts_per_page

    else:

        posts_per_page = 9
    paginator = Paginator(
        posts,
        posts_per_page
    )

    page_number = request.GET.get(
        'page'
    )

    page_obj = paginator.get_page(
        page_number
    )
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
    return render(
        request,
        "blog/post_list.html",
        context
    )

@login_required(login_url='login')
@permission_required(
    'blog.add_blogpost',
    raise_exception=True
)
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

    publish_due_posts()

    # 410 Gone
    gone = GoneURL.objects.filter(
        path=request.path,
        is_active=True
    ).exists()

    if gone:
        return HttpResponseGone(
            'This page has been permanently removed.'
        )


    # Current published post
    try:

        post = (
            BlogPost.objects
            .select_related(
                "author_user",
                "category"
            )
            .prefetch_related(
                "tags"
            )
            .get(
                slug=slug,
                status='published',
                published_at__lte=timezone.now()
            )
        )

    except BlogPost.DoesNotExist:

        # Old slug -> 301
        old_slug = (
            BlogSlugRedirect.objects
            .select_related('post')
            .filter(
                old_slug=slug,
                post__status='published',
                post__published_at__lte=timezone.now()
            )
            .first()
        )

        if old_slug:

            return redirect(
                old_slug.post.get_absolute_url(),
                permanent=True
            )

        raise Http404


    cover = (
        BlogPostMedia.objects
        .filter(
            post=post,
            purpose=BlogPostMedia.Purpose.COVER,
            is_active=True
        )
        .select_related(
            'media_asset'
        )
        .first()
    )


    # Prevent duplicate views on the same day
    view_key = (
        f'post_view_{post.id}_'
        f'{timezone.localdate()}'
    )

    if not request.session.get(view_key):

        add_view(post)

        request.session[view_key] = True


    # Related posts
    post_tags = post.tags.all()

    related_posts = (
        BlogPost.objects
        .filter(
            status='published',
            published_at__lte=timezone.now()
        )
        .exclude(
            id=post.id
        )
        .filter(
            Q(category=post.category)
            |
            Q(tags__in=post_tags)
        )
        .distinct()
        .order_by(
            '-published_at'
        )[:4]
    )


    return render(
        request,
        'blog/post_detail.html',
        {
            'post': post,
            'cover': cover,
            'related_posts': related_posts,
        }
    )