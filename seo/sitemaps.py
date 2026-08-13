from django.contrib.sitemaps import Sitemap
from blog.models import BlogPost


class BlogPostSitemap(Sitemap):

    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return BlogPost.objects.filter(
            status="published"
        )

    def lastmod(self, obj):
        return obj.updated_at