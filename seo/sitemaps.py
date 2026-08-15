from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from blog.models import BlogPost, BlogCategory


class BlogPostSitemap(Sitemap):

    changefreq = 'weekly'
    priority = 0.8

    def items(self):

        return BlogPost.objects.filter(
            status='published',
            published_at__lte=timezone.now()
        )

    def lastmod(self, obj):

        return obj.updated_at



class BlogCategorySitemap(Sitemap):

    changefreq = 'weekly'
    priority = 0.6

    def items(self):

        return BlogCategory.objects.filter(
            is_active=True,
            posts__status='published',
            posts__published_at__lte=timezone.now()
        ).distinct()

    def location(self, obj):

        return (
            reverse('blog:post_list')
            + f'?category={obj.slug}'
        )



class AuthorSitemap(Sitemap):

    changefreq = 'weekly'
    priority = 0.6

    def items(self):

        return User.objects.filter(
            is_active=True,
            blog_posts__status='published',
            blog_posts__published_at__lte=timezone.now()
        ).distinct()

    def location(self, obj):

        return reverse(
            'author_profile',
            kwargs={
                'username': obj.username
            }
        )